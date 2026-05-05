import os, pytest
os.environ.setdefault("GOOGLE_API_KEY", "test")
os.environ.setdefault("SECRET_PANEL", "testpass")

import database
from database import init_db, insert_candidate, get_candidate
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    init_db()

@pytest.fixture
def client(tmp_db):
    from main import app
    return TestClient(app)

@pytest.fixture
def cid(tmp_db):
    return insert_candidate(
        name="Ana López", email="ana@test.com", phone="",
        cv_filename="cv.pdf", cv_original_name="cv.pdf",
        score=8.0, score_label="Excelente", years_experience=4,
        education_level="Licenciatura", matching_skills='[]',
        summary="", strength="", weaknesses='[]', full_analysis='{}',
        availability="Inmediata", expected_salary="35000", specific_experience="Dev"
    )

HEADERS = {"X-Recruiter-Password": "testpass"}

def test_aceptar_actualiza_estado(client, cid):
    r = client.post(f"/api/candidatos/{cid}/aceptar",
                    json={"fecha_inicio": "2026-06-01"}, headers=HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "email_sent" in body
    c = get_candidate(cid)
    assert c["estado"] == "aceptado"
    assert c["fecha_inicio"] == "2026-06-01"

def test_agendar_actualiza_estado(client, cid):
    r = client.post(f"/api/candidatos/{cid}/agendar",
                    json={"fecha_cita": "2026-05-20", "hora_cita": "10:00", "notas": "Por Zoom"},
                    headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["success"] is True
    c = get_candidate(cid)
    assert c["estado"] == "agendado"
    assert c["fecha_cita"] == "2026-05-20"
    assert c["hora_cita"] == "10:00"
    assert c["notas_cita"] == "Por Zoom"

def test_agendar_sin_notas(client, cid):
    r = client.post(f"/api/candidatos/{cid}/agendar",
                    json={"fecha_cita": "2026-05-20", "hora_cita": "10:00"},
                    headers=HEADERS)
    assert r.status_code == 200
    assert get_candidate(cid)["estado"] == "agendado"

def test_rechazar_actualiza_estado(client, cid):
    r = client.post(f"/api/candidatos/{cid}/rechazar", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert get_candidate(cid)["estado"] == "rechazado"

def test_aceptar_candidato_inexistente(client):
    r = client.post("/api/candidatos/9999/aceptar",
                    json={"fecha_inicio": "2026-06-01"}, headers=HEADERS)
    assert r.status_code == 404

def test_agendar_candidato_inexistente(client):
    r = client.post("/api/candidatos/9999/agendar",
                    json={"fecha_cita": "2026-05-20", "hora_cita": "10:00"},
                    headers=HEADERS)
    assert r.status_code == 404

def test_rechazar_candidato_inexistente(client):
    r = client.post("/api/candidatos/9999/rechazar", headers=HEADERS)
    assert r.status_code == 404

def test_endpoints_requieren_auth(client, cid):
    assert client.post(f"/api/candidatos/{cid}/aceptar",
                       json={"fecha_inicio": "2026-06-01"}).status_code == 401
    assert client.post(f"/api/candidatos/{cid}/agendar",
                       json={"fecha_cita": "2026-05-20", "hora_cita": "10:00"}).status_code == 401
    assert client.post(f"/api/candidatos/{cid}/rechazar").status_code == 401
