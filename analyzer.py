import os, re, json, io
import pdfplumber
from groq import Groq

def _get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT = """Eres un experto en recursos humanos. Analiza el siguiente CV.
Responde ÚNICAMENTE con un objeto JSON válido (sin markdown, sin texto adicional) con esta estructura exacta:
{
  "nombre": "nombre completo del candidato",
  "años_experiencia": 0,
  "nivel_estudios": "nivel académico más alto",
  "habilidades_coincidentes": ["habilidad1", "habilidad2"],
  "puntaje": 7,
  "resumen": "resumen ejecutivo del candidato",
  "fortaleza": "principal fortaleza detectada",
  "debilidades": ["área de oportunidad 1", "área de oportunidad 2"]
}
Criterio de puntaje: 9-10 excepcional, 7-8 muy bueno, 5-6 adecuado, 3-4 con carencias, 1-2 no apto.
CV a analizar:
{CV_TEXT}"""

def score_label(score: float) -> str:
    if score >= 8:
        return "Excelente"
    if score >= 5:
        return "Bueno"
    return "En desarrollo"

def _parse_analysis(raw: str) -> dict:
    try:
        match = re.search(r'\{[\s\S]*\}', raw)
        analysis = json.loads(match.group(0) if match else raw)
        analysis["score_label"] = score_label(analysis.get("puntaje", 5))
        return analysis
    except Exception:
        return {
            "nombre": "No identificado", "años_experiencia": 0,
            "nivel_estudios": "No especificado", "habilidades_coincidentes": [],
            "puntaje": 5, "score_label": "Bueno",
            "resumen": "Análisis no disponible.", "fortaleza": "",
            "debilidades": ["Revisar CV manualmente", "Formato no procesable"]
        }

def extract_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def analyze_cv(pdf_bytes: bytes) -> dict:
    text = extract_text(pdf_bytes)
    if not text or len(text.strip()) < 30:
        raise ValueError("El PDF no contiene texto legible.")
    prompt = PROMPT.replace("{CV_TEXT}", text[:12000])
    completion = _get_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_analysis(completion.choices[0].message.content.strip())
