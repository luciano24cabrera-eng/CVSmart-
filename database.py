import sqlite3, json
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "cvsmart.db"

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                cv_filename TEXT NOT NULL,
                cv_original_name TEXT,
                score REAL DEFAULT 0,
                score_label TEXT,
                years_experience REAL,
                education_level TEXT,
                matching_skills TEXT DEFAULT '[]',
                summary TEXT,
                strength TEXT,
                weaknesses TEXT DEFAULT '[]',
                full_analysis TEXT DEFAULT '{}',
                availability TEXT,
                expected_salary TEXT,
                specific_experience TEXT,
                email_sent INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def insert_candidate(**kwargs) -> int:
    with _conn() as conn:
        cur = conn.execute("""
            INSERT INTO candidates (
                name, email, phone, cv_filename, cv_original_name,
                score, score_label, years_experience, education_level,
                matching_skills, summary, strength, weaknesses,
                full_analysis, availability, expected_salary, specific_experience
            ) VALUES (
                :name, :email, :phone, :cv_filename, :cv_original_name,
                :score, :score_label, :years_experience, :education_level,
                :matching_skills, :summary, :strength, :weaknesses,
                :full_analysis, :availability, :expected_salary, :specific_experience
            )
        """, kwargs)
        conn.commit()
        return cur.lastrowid

def get_all_candidates() -> list:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT id, name, email, phone, score, score_label, years_experience,
                   education_level, matching_skills, summary, strength, weaknesses,
                   availability, expected_salary, specific_experience,
                   cv_original_name, email_sent, created_at
            FROM candidates ORDER BY score DESC, created_at DESC
        """).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["matching_skills"] = json.loads(d["matching_skills"] or "[]")
            d["weaknesses"] = json.loads(d["weaknesses"] or "[]")
            result.append(d)
        return result

def get_stats() -> dict:
    with _conn() as conn:
        row = conn.execute("""
            SELECT COUNT(*) as total,
                   ROUND(AVG(score), 1) as avg_score,
                   COUNT(CASE WHEN score >= 8 THEN 1 END) as high_score,
                   COUNT(CASE WHEN score >= 5 AND score < 8 THEN 1 END) as mid_score,
                   COUNT(CASE WHEN score < 5 THEN 1 END) as low_score
            FROM candidates
        """).fetchone()
        return dict(row)

def get_candidate(candidate_id: int) -> Optional[dict]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["matching_skills"] = json.loads(d["matching_skills"] or "[]")
        d["weaknesses"] = json.loads(d["weaknesses"] or "[]")
        d["full_analysis"] = json.loads(d["full_analysis"] or "{}")
        return d

def mark_email_sent(candidate_id: int):
    with _conn() as conn:
        conn.execute("UPDATE candidates SET email_sent = 1 WHERE id = ?", (candidate_id,))
        conn.commit()
