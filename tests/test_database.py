import os, pytest
os.environ.setdefault("GOOGLE_API_KEY", "test")

from database import init_db, insert_candidate, get_all_candidates, get_stats, get_candidate, mark_email_sent
import database, sqlite3
from pathlib import Path

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    init_db()

def test_init_creates_table(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "t.db")
    init_db()
    conn = sqlite3.connect(tmp_path / "t.db")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    assert ("candidates",) in tables

def test_insert_and_get():
    cid = insert_candidate(
        name="Juan Pérez", email="j@test.com", phone="", cv_filename="cv.pdf",
        cv_original_name="cv.pdf", score=8.0, score_label="Excelente",
        years_experience=5, education_level="Licenciatura",
        matching_skills='["Python"]', summary="Resumen", strength="Técnico",
        weaknesses='["Área 1"]', full_analysis='{}',
        availability="Inmediata", expected_salary="30000", specific_experience="Dev"
    )
    assert cid > 0
    candidate = get_candidate(cid)
    assert candidate["name"] == "Juan Pérez"
    assert candidate["matching_skills"] == ["Python"]

def test_get_stats():
    insert_candidate(
        name="A", email="a@test.com", phone="", cv_filename="a.pdf",
        cv_original_name="a.pdf", score=9.0, score_label="Excelente",
        years_experience=3, education_level="Maestría",
        matching_skills='[]', summary="", strength="", weaknesses='[]',
        full_analysis='{}', availability="Inmediata", expected_salary="40000",
        specific_experience=""
    )
    stats = get_stats()
    assert stats["total"] == 1
    assert stats["high_score"] == 1

def test_mark_email_sent():
    cid = insert_candidate(
        name="B", email="b@test.com", phone="", cv_filename="b.pdf",
        cv_original_name="b.pdf", score=6.0, score_label="Bueno",
        years_experience=2, education_level="Técnico",
        matching_skills='[]', summary="", strength="", weaknesses='[]',
        full_analysis='{}', availability="2 semanas", expected_salary="20000",
        specific_experience=""
    )
    mark_email_sent(cid)
    assert get_candidate(cid)["email_sent"] == 1

def test_get_all_candidates():
    insert_candidate(
        name="C1", email="c1@test.com", phone="", cv_filename="c1.pdf",
        cv_original_name="c1.pdf", score=9.0, score_label="Excelente",
        years_experience=5, education_level="Maestría",
        matching_skills='["Python", "SQL"]', summary="S1", strength="F1",
        weaknesses='["W1"]', full_analysis='{}',
        availability="Inmediata", expected_salary="50000", specific_experience="Dev"
    )
    insert_candidate(
        name="C2", email="c2@test.com", phone="", cv_filename="c2.pdf",
        cv_original_name="c2.pdf", score=5.0, score_label="Bueno",
        years_experience=2, education_level="Licenciatura",
        matching_skills='[]', summary="S2", strength="F2",
        weaknesses='[]', full_analysis='{}',
        availability="2 semanas", expected_salary="25000", specific_experience="QA"
    )
    candidates = get_all_candidates()
    assert len(candidates) == 2
    assert candidates[0]["score"] == 9.0  # ordered by score DESC
    assert candidates[0]["matching_skills"] == ["Python", "SQL"]  # JSON deserialized
    assert "full_analysis" not in candidates[0]  # not included in list view

def test_get_stats_empty():
    stats = get_stats()
    assert stats["total"] == 0
    assert stats["avg_score"] == 0.0

from database import update_candidate_estado

def _make_candidate():
    return insert_candidate(
        name="Test User", email="t@test.com", phone="", cv_filename="t.pdf",
        cv_original_name="t.pdf", score=7.0, score_label="Bueno",
        years_experience=2, education_level="Licenciatura",
        matching_skills='[]', summary="", strength="", weaknesses='[]',
        full_analysis='{}', availability="Inmediata",
        expected_salary="25000", specific_experience=""
    )

def test_candidate_has_estado_column():
    cid = _make_candidate()
    c = get_candidate(cid)
    assert c["estado"] == "pendiente"

def test_update_candidate_estado_aceptado():
    cid = _make_candidate()
    result = update_candidate_estado(cid, "aceptado", fecha_inicio="2026-06-01")
    assert result is True
    c = get_candidate(cid)
    assert c["estado"] == "aceptado"
    assert c["fecha_inicio"] == "2026-06-01"

def test_update_candidate_estado_agendado():
    cid = _make_candidate()
    result = update_candidate_estado(
        cid, "agendado",
        fecha_cita="2026-05-20", hora_cita="10:00", notas_cita="Zoom"
    )
    assert result is True
    c = get_candidate(cid)
    assert c["estado"] == "agendado"
    assert c["fecha_cita"] == "2026-05-20"
    assert c["hora_cita"] == "10:00"
    assert c["notas_cita"] == "Zoom"

def test_update_candidate_estado_rechazado():
    cid = _make_candidate()
    result = update_candidate_estado(cid, "rechazado")
    assert result is True
    assert get_candidate(cid)["estado"] == "rechazado"

def test_update_candidate_estado_not_found():
    result = update_candidate_estado(9999, "aceptado")
    assert result is False

def test_get_all_candidates_includes_estado():
    _make_candidate()
    candidates = get_all_candidates()
    assert "estado" in candidates[0]
