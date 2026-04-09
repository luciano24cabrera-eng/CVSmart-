from cv_generator import generate_cv_pdf

SAMPLE_CV = {
    "nombre": "Juan Pérez",
    "contacto": {"email": "juan@example.com", "telefono": "5551234567"},
    "puesto_objetivo": "Desarrollador Python",
    "resumen_profesional": "Profesional con 5 años de experiencia en desarrollo backend.",
    "experiencia": [{
        "empresa": "TechCo", "puesto": "Desarrollador Senior",
        "periodo": "2020–2024",
        "logros": ["Desarrollé API REST para 50k usuarios", "Reduje latencia en 40%"]
    }],
    "educacion": [{"institucion": "UNAM", "carrera": "Ing. en Sistemas", "año": "2019"}],
    "habilidades_tecnicas": ["Python", "FastAPI", "PostgreSQL"],
    "habilidades_blandas": ["Trabajo en equipo", "Comunicación efectiva"],
    "idiomas": ["Español (nativo)", "Inglés (B2)"]
}

def test_returns_bytes():
    pdf = generate_cv_pdf(SAMPLE_CV)
    assert isinstance(pdf, bytes)

def test_is_valid_pdf():
    pdf = generate_cv_pdf(SAMPLE_CV)
    assert pdf[:4] == b"%PDF"

def test_has_content():
    pdf = generate_cv_pdf(SAMPLE_CV)
    assert len(pdf) > 1000
