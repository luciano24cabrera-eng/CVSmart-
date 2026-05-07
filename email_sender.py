import os, json
import html as _html
import urllib.request

_BADGE = {
    "Excelente": ("#166534", "#dcfce7"),
    "Bueno":     ("#92400e", "#fef3c7"),
    "En desarrollo": ("#991b1b", "#fee2e2"),
}

_WRAPPER_STYLE = "max-width:600px;margin:32px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(31,56,100,.1)"
_HEADER_STYLE  = "background:linear-gradient(135deg,#1F3864,#2E75B6);padding:32px;text-align:center"

def _send_html_email(to_email: str, subject: str, html_body: str) -> bool:
    api_key  = os.getenv("RESEND_API_KEY")
    from_addr = os.getenv("RESEND_FROM", "onboarding@resend.dev")
    if not api_key:
        print("⚠️  Email no enviado: RESEND_API_KEY no configurado")
        return False
    payload = json.dumps({
        "from": from_addr,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        print(f"⚠️  Error enviando email a {to_email}: {e}")
        return False

def _email_wrapper(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F8FAFF;font-family:Arial,sans-serif">
  <div style="{_WRAPPER_STYLE}">
    <div style="{_HEADER_STYLE}">
      <h1 style="color:#fff;margin:0;font-size:26px">🧠 CVSmart</h1>
      <p style="color:rgba(255,255,255,.8);margin:8px 0 0">Sistema inteligente de filtrado de CVs</p>
    </div>
    <div style="padding:32px">{body_html}</div>
    <div style="background:#F8FAFF;padding:16px;text-align:center;color:#9ca3af;font-size:12px">
      <p style="margin:0">Equipo CVSmart &copy; 2026 — Este correo fue generado automáticamente.</p>
    </div>
  </div>
</body>
</html>"""

def build_email_html(name: str, score_label: str, strength: str, weaknesses: list) -> str:
    color, bg = _BADGE.get(score_label, ("#374151", "#f3f4f6"))
    safe_name = _html.escape(name)
    safe_strength = _html.escape(strength)
    wk_items = "".join(f"<li style='margin-bottom:6px'>{_html.escape(w)}</li>" for w in weaknesses)
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    body = f"""
      <p style="font-size:16px">Hola <strong>{safe_name}</strong>,</p>
      <p style="color:#4b5563">Recibimos tu CV y lo analizamos con nuestra IA. Aquí está tu retroalimentación personalizada:</p>
      <div style="margin:24px 0">
        <p style="font-weight:bold;color:#1F3864;margin-bottom:8px">Tu nivel de perfil:</p>
        <span style="background:{bg};color:{color};padding:8px 20px;border-radius:20px;font-weight:bold;font-size:15px">{score_label}</span>
      </div>
      <div style="margin:24px 0">
        <p style="font-weight:bold;color:#1F3864;margin-bottom:8px">Tu principal fortaleza:</p>
        <p style="background:#F0F7FF;border-left:4px solid #2E75B6;padding:12px 16px;border-radius:0 8px 8px 0;margin:0">{safe_strength}</p>
      </div>
      <div style="margin:24px 0">
        <p style="font-weight:bold;color:#1F3864;margin-bottom:8px">Áreas de oportunidad:</p>
        <ul style="color:#4b5563;padding-left:20px">{wk_items}</ul>
      </div>
      <p style="color:#4b5563">¿Quieres un CV más profesional? Usa nuestro Creador de CV con IA:</p>
      <a href="{base_url}/crear-cv"
         style="display:block;background:linear-gradient(135deg,#1F3864,#2E75B6);color:#fff;text-decoration:none;padding:14px 32px;border-radius:12px;text-align:center;font-weight:bold;margin:16px 0">
        Crear mi CV profesional →
      </a>"""
    return _email_wrapper(body)

def _build_aceptado_html(name: str, empresa: str, fecha_inicio: str) -> str:
    safe_name    = _html.escape(name)
    safe_empresa = _html.escape(empresa)
    safe_fecha   = _html.escape(fecha_inicio)
    body = f"""
      <p style="font-size:16px">Estimado/a <strong>{safe_name}</strong>,</p>
      <p style="color:#4b5563">Nos complace informarte que has sido seleccionado/a para formar parte de nuestro equipo.</p>
      <div style="margin:24px 0;background:#F0FFF4;border-left:4px solid #22c55e;padding:16px 20px;border-radius:0 8px 8px 0;">
        <p style="margin:0;font-size:15px">📅 Tu fecha de inicio es: <strong>{safe_fecha}</strong></p>
      </div>
      <p style="color:#4b5563">En los próximos días recibirás más detalles sobre tu incorporación.</p>
      <p style="color:#4b5563">¡Bienvenido/a a bordo!</p>
      <p style="color:#4b5563;margin-top:24px">Atentamente,<br><strong>Equipo de Reclutamiento</strong><br>{safe_empresa}</p>"""
    return _email_wrapper(body)

def _build_agendado_html(name: str, empresa: str, fecha_cita: str, hora_cita: str, notas: str) -> str:
    safe_name    = _html.escape(name)
    safe_empresa = _html.escape(empresa)
    safe_fecha   = _html.escape(fecha_cita)
    safe_hora    = _html.escape(hora_cita)
    notas_line   = (
        f"<p style='margin:8px 0 0'>📝 Detalles: {_html.escape(notas)}</p>"
        if notas.strip() else ""
    )
    body = f"""
      <p style="font-size:16px">Estimado/a <strong>{safe_name}</strong>,</p>
      <p style="color:#4b5563">Hemos agendado una cita contigo para continuar con tu proceso de selección.</p>
      <div style="margin:24px 0;background:#EFF6FF;border-left:4px solid #3b82f6;padding:16px 20px;border-radius:0 8px 8px 0;">
        <p style="margin:0">📅 Fecha: <strong>{safe_fecha}</strong></p>
        <p style="margin:8px 0 0">🕐 Hora: <strong>{safe_hora}</strong></p>
        {notas_line}
      </div>
      <p style="color:#4b5563">Por favor confirma tu asistencia respondiendo este correo.</p>
      <p style="color:#4b5563;margin-top:24px">Atentamente,<br><strong>Equipo de Reclutamiento</strong><br>{safe_empresa}</p>"""
    return _email_wrapper(body)

def _build_rechazado_html(name: str, empresa: str) -> str:
    safe_name    = _html.escape(name)
    safe_empresa = _html.escape(empresa)
    body = f"""
      <p style="font-size:16px">Estimado/a <strong>{safe_name}</strong>,</p>
      <p style="color:#4b5563">Agradecemos sinceramente el tiempo y el esfuerzo que dedicaste a tu postulación en <strong>{safe_empresa}</strong>.</p>
      <p style="color:#4b5563">Luego de una cuidadosa evaluación, hemos decidido continuar el proceso con otros candidatos cuyo perfil se ajusta más a las necesidades actuales del puesto.</p>
      <p style="color:#4b5563">Esta decisión no refleja tu valor profesional. Te animamos a seguir adelante y a postularte en futuras oportunidades con nosotros.</p>
      <p style="color:#4b5563">¡Mucho éxito en tu búsqueda!</p>
      <p style="color:#4b5563;margin-top:24px">Atentamente,<br><strong>Equipo de Reclutamiento</strong><br>{safe_empresa}</p>"""
    return _email_wrapper(body)

def send_action_email(to_email: str, name: str, action: str, **kwargs) -> bool:
    empresa = os.getenv("NOMBRE_EMPRESA", "CVSmart")
    builders = {
        "aceptado": lambda: (
            f"¡Felicidades! Has sido aceptado en {empresa}",
            _build_aceptado_html(name, empresa, kwargs.get("fecha_inicio", ""))
        ),
        "agendado": lambda: (
            f"Tienes una cita agendada con {empresa}",
            _build_agendado_html(name, empresa, kwargs.get("fecha_cita", ""), kwargs.get("hora_cita", ""), kwargs.get("notas", ""))
        ),
        "rechazado": lambda: (
            f"Actualización sobre tu proceso de selección en {empresa}",
            _build_rechazado_html(name, empresa)
        ),
    }
    if action not in builders:
        return False
    subject, html = builders[action]()
    return _send_html_email(to_email, subject, html)

def send_feedback_email(to_email: str, name: str, score_label: str, strength: str, weaknesses: list) -> bool:
    subject = "CVSmart — Recibimos tu CV, aquí está tu retroalimentación"
    html_body = build_email_html(name, score_label, strength, weaknesses)
    return _send_html_email(to_email, subject, html_body)
