import os, re, json, io
import threading
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

_client = None
_client_lock = threading.Lock()

def _get_client() -> Groq:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client

IMPROVE_PROMPT = """Eres un experto en recursos humanos y redacción de CVs profesionales en México.
Con los siguientes datos del candidato, genera un CV completo, profesional y bien redactado.
Mejora la redacción manteniendo la información original.
Devuelve SOLO un JSON válido sin markdown con esta estructura exacta:
{
  "nombre": "",
  "contacto": {"email": "", "telefono": ""},
  "puesto_objetivo": "",
  "resumen_profesional": "párrafo mejorado y profesional",
  "experiencia": [{"empresa": "", "puesto": "", "periodo": "", "logros": ["logro 1", "logro 2"]}],
  "educacion": [{"institucion": "", "carrera": "", "año": ""}],
  "habilidades_tecnicas": [],
  "habilidades_blandas": [],
  "idiomas": []
}
Datos del candidato: {datos}"""

def improve_cv_with_ai(cv_data: dict) -> dict:
    prompt = IMPROVE_PROMPT.replace("{datos}", json.dumps(cv_data, ensure_ascii=False))
    try:
        completion = _get_client().chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        raise RuntimeError(f"Error al conectar con la IA: {e}") from e
    raw = completion.choices[0].message.content.strip()
    try:
        match = re.search(r'\{[\s\S]*\}', raw)
        return json.loads(match.group(0) if match else raw)
    except (json.JSONDecodeError, AttributeError):
        raise ValueError(f"La IA devolvió un formato inesperado: {raw[:100]}")

def generate_cv_pdf(cv: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    navy  = colors.HexColor("#1F3864")
    blue  = colors.HexColor("#2E75B6")
    gray  = colors.HexColor("#4b5563")

    def style(name, **kw):
        defaults = dict(fontName="Helvetica", fontSize=10, leading=14, textColor=gray)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    name_st    = style("Name",    fontName="Helvetica-Bold", fontSize=22, textColor=navy, leading=26)
    contact_st = style("Contact", fontSize=10, textColor=blue)
    section_st = style("Section", fontName="Helvetica-Bold", fontSize=12, textColor=navy, spaceBefore=14)
    body_st    = style("Body")
    bullet_st  = style("Bullet",  leftIndent=12)

    def hr(): return HRFlowable(width="100%", color=blue, thickness=1, spaceAfter=6)

    story = []
    story.append(Paragraph(cv.get("nombre", ""), name_st))
    c = cv.get("contacto", {})
    story.append(Paragraph(f"{c.get('email','')}  |  {c.get('telefono','')}", contact_st))
    if cv.get("puesto_objetivo"):
        story.append(Paragraph(f"<b>Puesto objetivo:</b> {cv['puesto_objetivo']}", body_st))
    story.append(HRFlowable(width="100%", color=navy, thickness=2, spaceBefore=8, spaceAfter=12))

    if cv.get("resumen_profesional"):
        story.append(Paragraph("Resumen Profesional", section_st)); story.append(hr())
        story.append(Paragraph(cv["resumen_profesional"], body_st))

    if cv.get("experiencia"):
        story.append(Paragraph("Experiencia Laboral", section_st)); story.append(hr())
        for exp in cv["experiencia"]:
            story.append(Paragraph(f"<b>{exp.get('puesto','')}</b> — {exp.get('empresa','')} ({exp.get('periodo','')})", body_st))
            for logro in exp.get("logros", []):
                story.append(Paragraph(f"• {logro}", bullet_st))
            story.append(Spacer(1, 6))

    if cv.get("educacion"):
        story.append(Paragraph("Educación", section_st)); story.append(hr())
        for edu in cv["educacion"]:
            story.append(Paragraph(f"<b>{edu.get('carrera','')}</b> — {edu.get('institucion','')} ({edu.get('año','')})", body_st))

    if cv.get("habilidades_tecnicas"):
        story.append(Paragraph("Habilidades Técnicas", section_st)); story.append(hr())
        story.append(Paragraph("  •  ".join(cv["habilidades_tecnicas"]), body_st))

    if cv.get("habilidades_blandas"):
        story.append(Paragraph("Habilidades Blandas", section_st)); story.append(hr())
        story.append(Paragraph("  •  ".join(cv["habilidades_blandas"]), body_st))

    if cv.get("idiomas"):
        story.append(Paragraph("Idiomas", section_st)); story.append(hr())
        story.append(Paragraph("  •  ".join(cv["idiomas"]), body_st))

    doc.build(story)
    return buffer.getvalue()
