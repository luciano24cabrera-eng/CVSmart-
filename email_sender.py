import os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_BADGE = {
    "Excelente": ("#166534", "#dcfce7"),
    "Bueno":     ("#92400e", "#fef3c7"),
    "En desarrollo": ("#991b1b", "#fee2e2"),
}

def build_email_html(name: str, score_label: str, strength: str, weaknesses: list) -> str:
    color, bg = _BADGE.get(score_label, ("#374151", "#f3f4f6"))
    wk_items = "".join(f"<li style='margin-bottom:6px'>{w}</li>" for w in weaknesses)
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F8FAFF;font-family:Arial,sans-serif">
  <div style="max-width:600px;margin:32px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(31,56,100,.1)">
    <div style="background:linear-gradient(135deg,#1F3864,#2E75B6);padding:32px;text-align:center">
      <h1 style="color:#fff;margin:0;font-size:26px">🧠 CVSmart</h1>
      <p style="color:rgba(255,255,255,.8);margin:8px 0 0">Sistema inteligente de filtrado de CVs</p>
    </div>
    <div style="padding:32px">
      <p style="font-size:16px">Hola <strong>{name}</strong>,</p>
      <p style="color:#4b5563">Recibimos tu CV y lo analizamos con nuestra IA. Aquí está tu retroalimentación personalizada:</p>
      <div style="margin:24px 0">
        <p style="font-weight:bold;color:#1F3864;margin-bottom:8px">Tu nivel de perfil:</p>
        <span style="background:{bg};color:{color};padding:8px 20px;border-radius:20px;font-weight:bold;font-size:15px">{score_label}</span>
      </div>
      <div style="margin:24px 0">
        <p style="font-weight:bold;color:#1F3864;margin-bottom:8px">Tu principal fortaleza:</p>
        <p style="background:#F0F7FF;border-left:4px solid #2E75B6;padding:12px 16px;border-radius:0 8px 8px 0;margin:0">{strength}</p>
      </div>
      <div style="margin:24px 0">
        <p style="font-weight:bold;color:#1F3864;margin-bottom:8px">Áreas de oportunidad:</p>
        <ul style="color:#4b5563;padding-left:20px">{wk_items}</ul>
      </div>
      <p style="color:#4b5563">¿Quieres un CV más profesional? Usa nuestro Creador de CV con IA:</p>
      <a href="http://localhost:8000/crear-cv"
         style="display:block;background:linear-gradient(135deg,#1F3864,#2E75B6);color:#fff;text-decoration:none;padding:14px 32px;border-radius:12px;text-align:center;font-weight:bold;margin:16px 0">
        Crear mi CV profesional →
      </a>
    </div>
    <div style="background:#F8FAFF;padding:16px;text-align:center;color:#9ca3af;font-size:12px">
      <p style="margin:0">Equipo CVSmart &copy; 2026 — Este correo fue generado automáticamente.</p>
    </div>
  </div>
</body>
</html>"""

def send_feedback_email(to_email: str, name: str, score_label: str, strength: str, weaknesses: list) -> bool:
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_user or not gmail_password:
        print("⚠️  Email no enviado: GMAIL_USER o GMAIL_APP_PASSWORD no configurados en .env")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "CVSmart — Recibimos tu CV, aquí está tu retroalimentación"
    msg["From"] = gmail_user
    msg["To"] = to_email
    msg.attach(MIMEText(build_email_html(name, score_label, strength, weaknesses), "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"⚠️  Error enviando email a {to_email}: {e}")
        return False
