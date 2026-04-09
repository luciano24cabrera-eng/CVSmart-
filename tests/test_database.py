import os, pytest
os.environ.setdefault("GROQ_API_KEY", "test")

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
