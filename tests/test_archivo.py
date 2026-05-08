import os, pytest
os.environ.setdefault("GOOGLE_API_KEY", "test")
os.environ.setdefault("SECRET_PANEL", "testpass")

import database
from database import (
    init_db, insert_candidate, get_all_candidates,
    get_archived_candidates, archive_candidate, unarchive_candidate,
)

_BASE = dict(
    name="Ana", email="ana@test.com", phone="",
    cv_filename="cv.pdf", cv_original_name="cv.pdf",
    score=8.0, score_label="Excelente", years_experience=3,
    education_level="Licenciatura", matching_skills='[]',
    summary="", strength="", weaknesses='[]', full_analysis='{}',
    availability="Inmediata", expected_salary="30000", specific_experience="Dev",
)

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    init_db()

@pytest.fixture
def cid():
    return insert_candidate(**_BASE)

def test_candidato_nuevo_no_esta_archivado(cid):
    candidates = get_all_candidates()
    assert any(c["id"] == cid for c in candidates)

def test_archivar_quita_del_dashboard(cid):
    archive_candidate(cid)
    assert not any(c["id"] == cid for c in get_all_candidates())

def test_archivar_aparece_en_historial(cid):
    archive_candidate(cid)
    assert any(c["id"] == cid for c in get_archived_candidates())

def test_desarchivar_regresa_al_dashboard(cid):
    archive_candidate(cid)
    unarchive_candidate(cid)
    assert any(c["id"] == cid for c in get_all_candidates())
    assert not any(c["id"] == cid for c in get_archived_candidates())

def test_archivar_preserva_estado(cid):
    from database import update_candidate_estado
    update_candidate_estado(cid, "rechazado")
    archive_candidate(cid)
    historial = get_archived_candidates()
    c = next(c for c in historial if c["id"] == cid)
    assert c["estado"] == "rechazado"

def test_archivar_candidato_inexistente_retorna_false():
    assert archive_candidate(9999) is False

def test_desarchivar_candidato_inexistente_retorna_false():
    assert unarchive_candidate(9999) is False

def test_archivar_dos_veces_retorna_false_segunda_vez(cid):
    assert archive_candidate(cid) is True
    assert archive_candidate(cid) is False

def test_desarchivar_dos_veces_retorna_false_segunda_vez(cid):
    archive_candidate(cid)
    assert unarchive_candidate(cid) is True
    assert unarchive_candidate(cid) is False

# ── Endpoint tests ────────────────────────────────────────────────────

from fastapi.testclient import TestClient

HEADERS = {"X-Recruiter-Password": "testpass"}

@pytest.fixture
def client(tmp_db):
    from main import app
    return TestClient(app)

@pytest.fixture
def cid_via_db():
    return insert_candidate(**_BASE)

def test_endpoint_archivar(client, cid_via_db):
    r = client.post(f"/api/candidatos/{cid_via_db}/archivar", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["success"] is True

def test_endpoint_archivar_quita_del_dashboard(client, cid_via_db):
    client.post(f"/api/candidatos/{cid_via_db}/archivar", headers=HEADERS)
    r = client.get("/api/panel/candidatos", headers=HEADERS)
    ids = [c["id"] for c in r.json()["candidates"]]
    assert cid_via_db not in ids

def test_endpoint_historial_muestra_archivados(client, cid_via_db):
    client.post(f"/api/candidatos/{cid_via_db}/archivar", headers=HEADERS)
    r = client.get("/api/panel/historial", headers=HEADERS)
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()["candidates"]]
    assert cid_via_db in ids

def test_endpoint_desarchivar(client, cid_via_db):
    client.post(f"/api/candidatos/{cid_via_db}/archivar", headers=HEADERS)
    r = client.post(f"/api/candidatos/{cid_via_db}/desarchivar", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["success"] is True

def test_endpoint_archivar_inexistente_retorna_404(client):
    r = client.post("/api/candidatos/9999/archivar", headers=HEADERS)
    assert r.status_code == 404

def test_endpoint_desarchivar_inexistente_retorna_404(client):
    r = client.post("/api/candidatos/9999/desarchivar", headers=HEADERS)
    assert r.status_code == 404

def test_endpoints_archivo_requieren_auth(client, cid_via_db):
    assert client.post(f"/api/candidatos/{cid_via_db}/archivar").status_code == 401
    assert client.post(f"/api/candidatos/{cid_via_db}/desarchivar").status_code == 401
    assert client.get("/api/panel/historial").status_code == 401
