import io, os, pytest
os.environ.setdefault("GOOGLE_API_KEY", "test")
os.environ.setdefault("SECRET_PANEL", "testpass")
os.environ["GEMINI_MOCK"] = "1"

import database
from database import init_db
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    init_db()

@pytest.fixture
def client(tmp_db, monkeypatch):
    import analyzer
    monkeypatch.setattr(analyzer, "extract_text", lambda _: "Soy desarrollador con 3 años de experiencia en Python.")
    from main import app
    return TestClient(app)

def _fake_pdf():
    return io.BytesIO(b"%PDF-1.4 fake content")

def test_aplicar_retorna_campos_de_analisis(client):
    r = client.post(
        "/api/aplicar",
        data={
            "email": "test@test.com",
            "phone": "",
            "availability": "Inmediata",
            "expected_salary": "30000",
            "specific_experience": "Python",
        },
        files={"cv": ("cv.pdf", _fake_pdf(), "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "score_label" in body
    assert body["score_label"] in {"Excelente", "Bueno", "En desarrollo"}
    assert "score" in body
    assert isinstance(body["score"], (int, float))
    assert "fortaleza" in body
    assert isinstance(body["fortaleza"], str)
    assert "debilidades" in body
    assert isinstance(body["debilidades"], list)
    assert "resumen" in body
    assert isinstance(body["resumen"], str)
