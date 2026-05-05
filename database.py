import sqlite3, json
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "cvsmart.db"

_CANDIDATE_FIELDS = {
    "name", "email", "phone", "cv_filename", "cv_original_name",
    "score", "score_label", "years_experience", "education_level",
    "matching_skills", "summary", "strength", "weaknesses",
    "full_analysis", "availability", "expected_salary", "specific_experience",
}

_NEW_COLS = [
    ("estado",       "TEXT DEFAULT 'pendiente'"),
    ("fecha_inicio", "TEXT"),
    ("fecha_cita",   "TEXT"),
    ("hora_cita",    "TEXT"),
    ("notas_cita",   "TEXT"),
]

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _migrate(conn):
    for col, col_def in _NEW_COLS:
        try:
            conn.execute(f"ALTER TABLE candidates ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass  # column already exists

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
        _migrate(conn)

def insert_candidate(**kwargs) -> int:
    unknown = set(kwargs) - _CANDIDATE_FIELDS
    if unknown:
        raise ValueError(f"Unknown candidate fields: {unknown}")
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
        return cur.lastrowid

def get_all_candidates() -> list:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT id, name, email, phone, score, score_label, years_experience,
                   education_level, matching_skills, summary, strength, weaknesses,
                   availability, expected_salary, specific_experience,
                   cv_original_name, email_sent, estado, created_at
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
        result = dict(row)
        result["avg_score"] = result["avg_score"] or 0.0
        return result

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

def update_candidate_estado(candidate_id: int, estado: str, **extra_fields) -> bool:
    allowed = {"fecha_inicio", "fecha_cita", "hora_cita", "notas_cita"}
    unknown = set(extra_fields) - allowed
    if unknown:
        raise ValueError(f"Unknown fields: {unknown}")
    fields = {"estado": estado, **extra_fields}
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    params = {**fields, "id": candidate_id}
    with _conn() as conn:
        cur = conn.execute(
            f"UPDATE candidates SET {set_clause} WHERE id = :id",
            params
        )
        return cur.rowcount > 0
