import os, re, json, io, time
import pdfplumber
from google import genai
from google.genai import types

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    return _client

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
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"⚠️  Could not parse Google AI response: {e}. Raw: {raw[:100]}")
        return {
            "nombre": "No identificado", "años_experiencia": 0,
            "nivel_estudios": "No especificado", "habilidades_coincidentes": [],
            "puntaje": 5, "score_label": "Bueno",
            "resumen": "Análisis no disponible.", "fortaleza": "",
            "debilidades": ["Revisar CV manualmente", "Formato no procesable"]
        }

def extract_text(pdf_bytes: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        raise ValueError(f"No se pudo leer el PDF: {e}") from e

def analyze_cv(pdf_bytes: bytes) -> dict:
    text = extract_text(pdf_bytes)
    if not text or len(text.strip()) < 30:
        raise ValueError("El PDF no contiene texto legible.")
    prompt = PROMPT.replace("{CV_TEXT}", text[:12000])
    if os.getenv("GEMINI_MOCK") == "1":
        return {
            "nombre": "Candidato Demo", "años_experiencia": 3,
            "nivel_estudios": "Licenciatura", "habilidades_coincidentes": ["Python", "SQL"],
            "puntaje": 7, "score_label": "Bueno",
            "resumen": "Candidato de prueba generado por mock.",
            "fortaleza": "Experiencia técnica sólida",
            "debilidades": ["Falta de experiencia en liderazgo", "Sin certificaciones"]
        }

    last_err = None
    for attempt in range(3):
        try:
            response = _get_client().models.generate_content(
                model=os.getenv("GOOGLE_MODEL", "gemini-flash-latest"),
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                ),
            )
            return _parse_analysis(response.text.strip())
        except Exception as e:
            last_err = e
            if "503" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            break
    raise RuntimeError(f"Error al conectar con la IA: {last_err}") from last_err
