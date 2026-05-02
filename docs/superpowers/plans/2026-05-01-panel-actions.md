# Panel Actions (Aprobar/Agendar/Descartar) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up the three modal action buttons in the recruiter panel so each one persists candidate status, sends an automatic email, and reflects status in the table via colored badges.

**Architecture:** Add three columns (`status`, `interview_at`, `interview_location`) to `candidates`. One new POST endpoint `/api/panel/candidatos/{cid}/accion` handles all three actions. Three email templates in `email_sender.py`. Frontend wires the existing buttons to a `doAction()` helper, adds a schedule mini-modal, a toast component, and status badges in both tables.

**Tech Stack:** FastAPI, SQLite, vanilla JS/HTML/CSS, smtplib (Gmail SMTP).

**Spec:** `docs/superpowers/specs/2026-05-01-panel-actions-design.md`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `database.py` | modify | Migration in `init_db`, new `update_candidate_status`, update SELECTs |
| `email_sender.py` | modify | New `send_action_email` + 3 HTML templates |
| `main.py` | modify | New POST endpoint for actions |
| `frontend/panel.html` | modify | Wire buttons, schedule sub-modal, toast, badges, status line |
| `tests/test_database.py` | modify | Tests for migration + `update_candidate_status` + extended SELECTs |
| `tests/test_panel_actions.py` | create | Endpoint tests using FastAPI TestClient |

---

## Task 1: Database migration — add three new columns to `candidates`

**Files:**
- Modify: `database.py:19-44` (`init_db` function)
- Test: `tests/test_database.py`

- [ ] **Step 1: Write failing test for migration on existing DB**

Add to `tests/test_database.py` (at the end of the file):

```python
def test_init_db_migrates_existing_table(tmp_path, monkeypatch):
    """init_db must add status/interview_at/interview_location columns to a pre-existing table that lacks them."""
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    # Create a legacy table WITHOUT the new columns
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cv_filename TEXT NOT NULL,
                score REAL DEFAULT 0
            )
        """)
        conn.execute("INSERT INTO candidates (name, cv_filename, score) VALUES ('Legacy', 'l.pdf', 7.0)")

    init_db()  # should add missing columns without losing data

    with sqlite3.connect(db_path) as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(candidates)").fetchall()}
        assert "status" in cols
        assert "interview_at" in cols
        assert "interview_location" in cols
        # Existing row preserved with default status
        row = conn.execute("SELECT name, status FROM candidates").fetchone()
        assert row == ("Legacy", "pending")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_database.py::test_init_db_migrates_existing_table -v`
Expected: FAIL with `assert "status" in cols` AssertionError.

- [ ] **Step 3: Update `init_db()` in `database.py` to add migration logic**

Replace the `init_db()` function in `database.py` (lines 19-44) with:

```python
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
                status TEXT DEFAULT 'pending',
                interview_at TEXT,
                interview_location TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migration for pre-existing DBs: add columns that don't exist yet.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(candidates)").fetchall()}
        if "status" not in existing:
            conn.execute("ALTER TABLE candidates ADD COLUMN status TEXT DEFAULT 'pending'")
        if "interview_at" not in existing:
            conn.execute("ALTER TABLE candidates ADD COLUMN interview_at TEXT")
        if "interview_location" not in existing:
            conn.execute("ALTER TABLE candidates ADD COLUMN interview_location TEXT")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_database.py -v`
Expected: ALL tests pass (including the new one and the existing `test_init_creates_table`).

- [ ] **Step 5: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "feat(db): add status/interview_at/interview_location columns with migration"
```

---

## Task 2: Add `update_candidate_status()` function to `database.py`

**Files:**
- Modify: `database.py` (add new function)
- Test: `tests/test_database.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_database.py` (at the end of the file):

```python
def test_update_candidate_status_approve():
    cid = insert_candidate(
        name="Test Approve", email="a@t.com", phone="", cv_filename="a.pdf",
        cv_original_name="a.pdf", score=8.0, score_label="Excelente",
        years_experience=3, education_level="Lic", matching_skills='[]',
        summary="", strength="", weaknesses='[]', full_analysis='{}',
        availability="Inmediata", expected_salary="30000", specific_experience=""
    )
    from database import update_candidate_status
    ok = update_candidate_status(cid, "approved")
    assert ok is True
    c = get_candidate(cid)
    assert c["status"] == "approved"
    assert c["interview_at"] is None
    assert c["interview_location"] is None

def test_update_candidate_status_schedule():
    cid = insert_candidate(
        name="Test Sched", email="s@t.com", phone="", cv_filename="s.pdf",
        cv_original_name="s.pdf", score=7.0, score_label="Bueno",
        years_experience=2, education_level="Lic", matching_skills='[]',
        summary="", strength="", weaknesses='[]', full_analysis='{}',
        availability="Inmediata", expected_salary="25000", specific_experience=""
    )
    from database import update_candidate_status
    ok = update_candidate_status(cid, "scheduled", "2026-06-15T10:00", "Google Meet")
    assert ok is True
    c = get_candidate(cid)
    assert c["status"] == "scheduled"
    assert c["interview_at"] == "2026-06-15T10:00"
    assert c["interview_location"] == "Google Meet"

def test_update_candidate_status_unknown_id():
    from database import update_candidate_status
    assert update_candidate_status(99999, "approved") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_database.py -k update_candidate_status -v`
Expected: FAIL with `ImportError: cannot import name 'update_candidate_status'`.

- [ ] **Step 3: Add `update_candidate_status()` to `database.py`**

Append to `database.py` (after `mark_email_sent` at the bottom):

```python
_VALID_STATUSES = {"pending", "approved", "scheduled", "rejected"}

def update_candidate_status(
    candidate_id: int,
    status: str,
    interview_at: Optional[str] = None,
    interview_location: Optional[str] = None,
) -> bool:
    """Update the candidate's status and (optionally) interview details.
    Returns True if a row was updated, False if no candidate has that id."""
    if status not in _VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE candidates SET status = ?, interview_at = ?, interview_location = ? WHERE id = ?",
            (status, interview_at, interview_location, candidate_id),
        )
        return cur.rowcount > 0
```

- [ ] **Step 4: Update `get_candidate()` and `get_all_candidates()` to expose new columns**

In `database.py`, replace the SELECT in `get_all_candidates()` (lines 67-81) with:

```python
def get_all_candidates() -> list:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT id, name, email, phone, score, score_label, years_experience,
                   education_level, matching_skills, summary, strength, weaknesses,
                   availability, expected_salary, specific_experience,
                   cv_original_name, email_sent, status, interview_at,
                   interview_location, created_at
            FROM candidates ORDER BY score DESC, created_at DESC
        """).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["matching_skills"] = json.loads(d["matching_skills"] or "[]")
            d["weaknesses"] = json.loads(d["weaknesses"] or "[]")
            result.append(d)
        return result
```

`get_candidate()` already uses `SELECT *` so no change needed there — the new columns will appear automatically.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_database.py -v`
Expected: ALL tests pass, including the three new `update_candidate_status` tests.

- [ ] **Step 6: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "feat(db): add update_candidate_status and expose status fields"
```

---

## Task 3: Add `send_action_email()` to `email_sender.py`

**Files:**
- Modify: `email_sender.py` (add new function and helpers)
- Test: `tests/test_email_sender.py` (create)

- [ ] **Step 1: Create test file with failing test**

Create `tests/test_email_sender.py`:

```python
import os
os.environ.setdefault("GOOGLE_API_KEY", "test")

from email_sender import build_action_email_html, format_interview_date

def test_format_interview_date_es():
    # ISO 8601 datetime-local format from frontend: "2026-05-15T10:00"
    formatted = format_interview_date("2026-05-15T10:00")
    assert "15" in formatted
    assert "mayo" in formatted.lower()
    assert "2026" in formatted
    assert "10:00" in formatted

def test_build_approve_email():
    html = build_action_email_html(name="Ana", action="approve")
    assert "Ana" in html
    assert "avanza" in html.lower() or "avanzas" in html.lower()
    assert "CVSmart" in html

def test_build_schedule_email_with_location():
    html = build_action_email_html(
        name="Luis", action="schedule",
        interview_at="2026-05-15T10:00",
        interview_location="Google Meet",
    )
    assert "Luis" in html
    assert "15" in html and "mayo" in html.lower()
    assert "Google Meet" in html

def test_build_schedule_email_without_location():
    html = build_action_email_html(
        name="Luis", action="schedule",
        interview_at="2026-05-15T10:00",
    )
    assert "Luis" in html
    assert "15" in html and "mayo" in html.lower()
    # No "Lugar:" line if no location
    assert "Lugar" not in html

def test_build_reject_email():
    html = build_action_email_html(name="Pedro", action="reject")
    assert "Pedro" in html
    assert "gracias" in html.lower()
    assert "no avanzaremos" in html.lower() or "no continuamos" in html.lower()

def test_build_email_unknown_action_raises():
    import pytest
    with pytest.raises(ValueError):
        build_action_email_html(name="X", action="unknown")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_email_sender.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_action_email_html' from 'email_sender'`.

- [ ] **Step 3: Add helpers and `send_action_email` to `email_sender.py`**

Append to `email_sender.py` (at the end of the file):

```python
_MONTHS_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

def format_interview_date(iso_str: str) -> str:
    """Format an ISO datetime string (e.g. '2026-05-15T10:00') as Spanish prose:
    '15 de mayo de 2026, 10:00 hrs'."""
    from datetime import datetime
    dt = datetime.fromisoformat(iso_str)
    return f"{dt.day} de {_MONTHS_ES[dt.month]} de {dt.year}, {dt.strftime('%H:%M')} hrs"

_ACTION_SUBJECTS = {
    "approve": "Avanzas en el proceso — CVSmart",
    "schedule": "Tu entrevista en CVSmart",
    "reject": "Resultado de tu postulación — CVSmart",
}

def _action_body(action: str, name: str, interview_at: str | None, interview_location: str | None) -> str:
    """Returns the inner HTML body for the given action."""
    safe_name = _html.escape(name)
    if action == "approve":
        return f"""
            <p style="font-size:16px">Hola <strong>{safe_name}</strong>,</p>
            <p style="color:#4b5563">¡Buenas noticias! Tu perfil avanza a la siguiente etapa del proceso.</p>
            <p style="color:#4b5563">Pronto nos pondremos en contacto contigo para los próximos pasos.</p>
            <p style="color:#4b5563">Gracias por confiar en nosotros.</p>
        """
    if action == "schedule":
        formatted = format_interview_date(interview_at) if interview_at else "—"
        location_line = (
            f'<p style="color:#4b5563"><strong>Lugar / Link:</strong> {_html.escape(interview_location)}</p>'
            if interview_location else ""
        )
        return f"""
            <p style="font-size:16px">Hola <strong>{safe_name}</strong>,</p>
            <p style="color:#4b5563">Te confirmamos tu entrevista en CVSmart.</p>
            <div style="margin:24px 0;background:#F0F7FF;border-left:4px solid #2E75B6;padding:16px;border-radius:0 8px 8px 0">
              <p style="margin:0 0 6px 0;color:#1F3864"><strong>Fecha y hora:</strong> {_html.escape(formatted)}</p>
              {location_line}
            </div>
            <p style="color:#4b5563">Te pedimos puntualidad. ¡Nos vemos pronto!</p>
        """
    if action == "reject":
        return f"""
            <p style="font-size:16px">Hola <strong>{safe_name}</strong>,</p>
            <p style="color:#4b5563">Gracias por aplicar a CVSmart y por el tiempo que dedicaste a tu postulación.</p>
            <p style="color:#4b5563">En esta ocasión no avanzaremos contigo en el proceso, pero te animamos a postularte a futuras oportunidades.</p>
            <p style="color:#4b5563">¡Mucho éxito en tu búsqueda!</p>
        """
    raise ValueError(f"Unknown action: {action}")

def build_action_email_html(
    name: str,
    action: str,
    interview_at: str | None = None,
    interview_location: str | None = None,
) -> str:
    body = _action_body(action, name, interview_at, interview_location)
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F8FAFF;font-family:Arial,sans-serif">
  <div style="max-width:600px;margin:32px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(31,56,100,.1)">
    <div style="background:linear-gradient(135deg,#1F3864,#2E75B6);padding:32px;text-align:center">
      <h1 style="color:#fff;margin:0;font-size:26px">🧠 CVSmart</h1>
      <p style="color:rgba(255,255,255,.8);margin:8px 0 0">Sistema inteligente de filtrado de CVs</p>
    </div>
    <div style="padding:32px">{body}</div>
    <div style="background:#F8FAFF;padding:16px;text-align:center;color:#9ca3af;font-size:12px">
      <p style="margin:0">Equipo CVSmart &copy; 2026 — Este correo fue generado automáticamente.</p>
    </div>
  </div>
</body>
</html>"""

def send_action_email(
    to_email: str,
    name: str,
    action: str,
    interview_at: str | None = None,
    interview_location: str | None = None,
) -> bool:
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_user or not gmail_password:
        print("⚠️  Email no enviado: GMAIL_USER o GMAIL_APP_PASSWORD no configurados en .env")
        return False
    if action not in _ACTION_SUBJECTS:
        raise ValueError(f"Unknown action: {action}")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = _ACTION_SUBJECTS[action]
    msg["From"] = gmail_user
    msg["To"] = to_email
    msg.attach(MIMEText(
        build_action_email_html(name, action, interview_at, interview_location),
        "html",
    ))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        return True
    except (smtplib.SMTPException, OSError) as e:
        print(f"⚠️  Error enviando email a {to_email}: {e}")
        return False
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_email_sender.py -v`
Expected: ALL 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add email_sender.py tests/test_email_sender.py
git commit -m "feat(email): add send_action_email with approve/schedule/reject templates"
```

---

## Task 4: Add `/api/panel/candidatos/{cid}/accion` endpoint

**Files:**
- Modify: `main.py:12` (extend import) and add new endpoint after `panel_cv` (around line 119)
- Test: `tests/test_panel_actions.py` (create)

- [ ] **Step 1: Create endpoint test file with failing tests**

Create `tests/test_panel_actions.py`:

```python
import os, sys
os.environ.setdefault("GOOGLE_API_KEY", "test")
os.environ.setdefault("SECRET_PANEL", "test-pwd")

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

import database
from database import init_db, insert_candidate

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    init_db()
    # Patch send_action_email to avoid SMTP
    import email_sender
    monkeypatch.setattr(email_sender, "send_action_email", lambda *a, **kw: True)
    # Re-import main with patched DB path
    if "main" in sys.modules:
        del sys.modules["main"]

@pytest.fixture
def client(tmp_db):
    from main import app
    return TestClient(app)

@pytest.fixture
def candidate_id():
    return insert_candidate(
        name="Test User", email="t@test.com", phone="", cv_filename="t.pdf",
        cv_original_name="t.pdf", score=8.0, score_label="Excelente",
        years_experience=3, education_level="Lic", matching_skills='[]',
        summary="", strength="", weaknesses='[]', full_analysis='{}',
        availability="Inmediata", expected_salary="30000", specific_experience="",
    )

AUTH = {"X-Recruiter-Password": "test-pwd"}

def test_action_requires_auth(client, candidate_id):
    r = client.post(f"/api/panel/candidatos/{candidate_id}/accion", json={"action": "approve"})
    assert r.status_code == 401

def test_action_approve(client, candidate_id):
    r = client.post(f"/api/panel/candidatos/{candidate_id}/accion",
                    json={"action": "approve"}, headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["status"] == "approved"
    assert body["email_sent"] is True

def test_action_reject(client, candidate_id):
    r = client.post(f"/api/panel/candidatos/{candidate_id}/accion",
                    json={"action": "reject"}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"

def test_action_schedule_requires_interview_at(client, candidate_id):
    r = client.post(f"/api/panel/candidatos/{candidate_id}/accion",
                    json={"action": "schedule"}, headers=AUTH)
    assert r.status_code == 400

def test_action_schedule_rejects_past_date(client, candidate_id):
    r = client.post(f"/api/panel/candidatos/{candidate_id}/accion",
                    json={"action": "schedule", "interview_at": "2020-01-01T10:00"},
                    headers=AUTH)
    assert r.status_code == 400

def test_action_schedule_success(client, candidate_id):
    r = client.post(f"/api/panel/candidatos/{candidate_id}/accion",
                    json={"action": "schedule", "interview_at": "2099-01-01T10:00",
                          "interview_location": "Google Meet"},
                    headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "scheduled"

def test_action_invalid_action(client, candidate_id):
    r = client.post(f"/api/panel/candidatos/{candidate_id}/accion",
                    json={"action": "destroy"}, headers=AUTH)
    assert r.status_code == 400

def test_action_unknown_candidate(client):
    r = client.post("/api/panel/candidatos/99999/accion",
                    json={"action": "approve"}, headers=AUTH)
    assert r.status_code == 404

def test_action_no_email_skips_send(client, monkeypatch):
    cid = insert_candidate(
        name="No Email", email="", phone="", cv_filename="n.pdf",
        cv_original_name="n.pdf", score=5.0, score_label="Bueno",
        years_experience=1, education_level="", matching_skills='[]',
        summary="", strength="", weaknesses='[]', full_analysis='{}',
        availability="", expected_salary="", specific_experience="",
    )
    r = client.post(f"/api/panel/candidatos/{cid}/accion",
                    json={"action": "approve"}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["email_sent"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_panel_actions.py -v`
Expected: FAIL — endpoint doesn't exist (404 on most tests).

- [ ] **Step 3: Update import on `main.py:12`**

Replace line 12 of `main.py`:

```python
from database import init_db, insert_candidate, get_all_candidates, get_stats, get_candidate, mark_email_sent, update_candidate_status
```

- [ ] **Step 4: Add import for `send_action_email` on `main.py:14`**

Replace line 14 of `main.py`:

```python
from email_sender import send_feedback_email, send_action_email
```

- [ ] **Step 5: Add the new endpoint to `main.py`**

Insert this AFTER the existing `panel_cv` endpoint (after line 119, before `# ── Generador de CV ──`):

```python
@app.post("/api/panel/candidatos/{cid}/accion")
def panel_action(cid: int, payload: dict = Body(...), _=Depends(require_auth)):
    from datetime import datetime

    action = payload.get("action")
    action_to_status = {"approve": "approved", "schedule": "scheduled", "reject": "rejected"}
    if action not in action_to_status:
        raise HTTPException(400, "Acción inválida. Debe ser approve, schedule o reject.")

    candidate = get_candidate(cid)
    if not candidate:
        raise HTTPException(404, "Candidato no encontrado")

    interview_at = payload.get("interview_at")
    interview_location = payload.get("interview_location") or None

    if action == "schedule":
        if not interview_at:
            raise HTTPException(400, "Falta interview_at para agendar.")
        try:
            dt = datetime.fromisoformat(interview_at)
        except ValueError:
            raise HTTPException(400, "Fecha inválida (formato ISO 8601 requerido).")
        if dt <= datetime.now():
            raise HTTPException(400, "La fecha de la entrevista debe ser futura.")
    else:
        # Approve/reject never carry interview details
        interview_at = None
        interview_location = None

    status = action_to_status[action]
    update_candidate_status(cid, status, interview_at, interview_location)

    email_sent = False
    if candidate.get("email"):
        try:
            email_sent = send_action_email(
                to_email=candidate["email"],
                name=candidate["name"],
                action=action,
                interview_at=interview_at,
                interview_location=interview_location,
            )
        except Exception as e:
            print(f"⚠️  Error en send_action_email: {e}")
            email_sent = False

    return {
        "success": True,
        "status": status,
        "interview_at": interview_at,
        "interview_location": interview_location,
        "email_sent": email_sent,
    }
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_panel_actions.py -v`
Expected: ALL 9 tests pass.

- [ ] **Step 7: Run the full test suite to make sure nothing broke**

Run: `pytest -v`
Expected: ALL tests pass.

- [ ] **Step 8: Commit**

```bash
git add main.py tests/test_panel_actions.py
git commit -m "feat(api): add POST /api/panel/candidatos/{cid}/accion endpoint"
```

---

## Task 5: Frontend — `doAction()` helper + wire up Aprobar and Descartar

**Files:**
- Modify: `frontend/panel.html` (script section, around lines 1209-1493)

This is a frontend-only task. No automated tests — verify manually by running the server.

- [ ] **Step 1: Add `doAction()` and `updateCachedCandidate()` helpers to the script**

In `frontend/panel.html`, find the `closeModal()` function (around line 1482-1484) and insert these new functions BEFORE it:

```javascript
  let _currentCandidateId = null;

  function updateCachedCandidate(id, fields) {
    const idx = _cachedCandidates.findIndex(c => c.id === id);
    if (idx !== -1) {
      _cachedCandidates[idx] = { ..._cachedCandidates[idx], ...fields };
    }
  }

  async function doAction(action, extras = {}) {
    if (_currentCandidateId == null) return;
    const id = _currentCandidateId;
    const body = { action, ...extras };
    let res;
    try {
      res = await fetch(`/api/panel/candidatos/${id}/accion`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Recruiter-Password': AUTH,
        },
        body: JSON.stringify(body),
      });
    } catch (err) {
      showToast('Error de conexión, intenta de nuevo', 'error');
      return;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || 'Error al ejecutar la acción', 'error');
      return;
    }
    const data = await res.json();
    updateCachedCandidate(id, {
      status: data.status,
      interview_at: data.interview_at,
      interview_location: data.interview_location,
    });
    closeModal();
    const messages = {
      approved:  'Candidato aprobado',
      scheduled: 'Entrevista agendada',
      rejected:  'Candidato descartado',
    };
    const variants = { approved: 'success-green', scheduled: 'success-yellow', rejected: 'success-red' };
    const suffix = data.email_sent ? ' · Email enviado' : (extras.skipEmailToast ? '' : ' · Sin email');
    showToast((messages[data.status] || 'Acción aplicada') + suffix, variants[data.status] || 'success-green');
    // Re-render both tables from cache
    renderMainTable(_cachedCandidates);
    renderCandidatesTable2(_cachedCandidates);
  }
```

- [ ] **Step 2: Extract main-table rendering into a reusable function**

In `frontend/panel.html`, find the part of `loadDashboard()` that builds `candidatesGrid.innerHTML` (lines 1389-1422). Refactor it into a separate `renderMainTable()` function. Replace lines 1389-1422 with:

```javascript
    renderMainTable(candidates);
```

And add this new function above `loadDashboard()` (before line 1365):

```javascript
  function renderMainTable(candidates) {
    const grid = document.getElementById('candidatesGrid');
    if (!grid) return;
    if (!candidates.length) {
      grid.innerHTML = `
        <tr><td colspan="7">
          <div class="empty-state">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
            No hay candidatos aún
          </div>
        </td></tr>`;
      return;
    }
    grid.innerHTML = candidates.map((c, i) => {
      const score   = parseFloat(c.score) || 0;
      const cls     = score >= 8 ? 'score-green' : score >= 6 ? 'score-yellow' : 'score-red';
      const rankNum = String(i + 1).padStart(2, '0');
      const badge   = renderStatusBadge(c);
      const rowCls  = c.status === 'rejected' ? 'row-rejected' : '';
      return `
        <tr class="${rowCls}" onclick="openModal(${c.id})">
          <td class="col-rank">${esc(rankNum)}</td>
          <td class="col-name">${esc(c.name)}${badge}</td>
          <td><span class="score-badge ${cls}">${esc(c.score)}</span></td>
          <td class="col-label">${esc(c.score_label || '—')}</td>
          <td class="col-label">${esc(c.years_experience ?? '—')} años</td>
          <td class="col-avail">${esc(c.availability || '—')}</td>
          <td class="col-actions" onclick="event.stopPropagation()">
            <button class="icon-btn" title="Descargar CV" onclick="downloadCV(${c.id})">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </button>
            <button class="icon-btn" title="Ver detalles" onclick="openModal(${c.id})">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </button>
          </td>
        </tr>`;
    }).join('');
  }
```

(`renderStatusBadge()` and the badge CSS will be added in Task 7. For now define a stub that returns `''`:)

```javascript
  function renderStatusBadge(_c) { return ''; }
```

(Place this stub right above `renderMainTable()`. Task 7 will replace it with the real implementation.)

- [ ] **Step 3: Wire up the modal action buttons in `openModal()`**

In `openModal()` in `frontend/panel.html`, find the line `document.getElementById('mDownloadBtn').onclick = () => downloadCV(id);` (line 1478) and insert ABOVE it:

```javascript
    _currentCandidateId = id;
    document.querySelector('.action-approve').onclick = () => doAction('approve');
    document.querySelector('.action-discard').onclick = () => {
      if (confirm('¿Descartar a este candidato? Se le enviará un email.')) doAction('reject');
    };
    document.querySelector('.action-schedule').onclick = () => showScheduleForm(id, c.name);
```

(`showScheduleForm` will be added in Task 6.)

- [ ] **Step 4: Add a temporary `showScheduleForm` and `showToast` stub**

These are needed so the JS doesn't error before Tasks 6 and 8 land. Add right above `closeModal()`:

```javascript
  function showScheduleForm(_id, _name) { alert('Pendiente: Task 6 — implementar mini-modal de agendar'); }
  function showToast(message, _variant) { console.log('[toast]', message); }
```

These will be replaced in Tasks 6 and 8.

- [ ] **Step 5: Manual smoke test — Approve and Reject**

1. Run the server: `python -m uvicorn main:app --reload`
2. Open `http://localhost:8000/panel`
3. Log in with the configured `SECRET_PANEL` password (default `cvsmart2026`).
4. Click on a candidate row to open the modal.
5. Click "Aprobar" → modal closes, console shows toast log, refresh page → candidate's status should still be "approved" in DB.
6. Verify with: `sqlite3 cvsmart.db "SELECT id, name, status FROM candidates WHERE status != 'pending';"`
7. Repeat for "Descartar" — confirm dialog appears, then status changes to "rejected".

Expected: Both buttons persist correctly. Schedule still shows the placeholder alert.

- [ ] **Step 6: Commit**

```bash
git add frontend/panel.html
git commit -m "feat(panel): wire up Aprobar/Descartar buttons to backend"
```

---

## Task 6: Frontend — Schedule mini-modal

**Files:**
- Modify: `frontend/panel.html` (CSS in `<style>` block + HTML inside modal + JS)

- [ ] **Step 1: Add CSS for the schedule form**

In `frontend/panel.html`, find the end of `.modal-actions` styles (around line 800, after `.action-discard:hover`). Add these new styles after `.action-discard:hover`:

```css
    /* Schedule form (sub-view of modal) */
    .schedule-form { padding: 1.75rem; }

    .schedule-form h3 {
      font-family: 'Poppins', sans-serif;
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }

    .schedule-form .schedule-sub {
      color: #a0a0a0;
      font-size: 0.85rem;
      margin-bottom: 1.5rem;
    }

    .schedule-form label {
      display: block;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #a0a0a0;
      margin: 1rem 0 6px;
    }

    .schedule-form input[type="datetime-local"],
    .schedule-form input[type="text"] {
      width: 100%;
      padding: 11px 14px;
      background: #111;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 8px;
      color: #fff;
      font-size: 0.9rem;
      font-family: inherit;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
      color-scheme: dark;
    }

    .schedule-form input:focus {
      outline: none;
      border-color: #e43c2f;
      box-shadow: 0 0 0 3px rgba(228, 60, 47, 0.12);
    }

    .schedule-form-actions {
      display: flex;
      gap: 8px;
      margin-top: 1.5rem;
    }

    .schedule-form .btn-cancel {
      flex: 1;
      padding: 11px;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 8px;
      background: transparent;
      color: #a0a0a0;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 600;
    }

    .schedule-form .btn-confirm {
      flex: 2;
      padding: 11px;
      background: #e43c2f;
      color: #fff;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 700;
    }

    .schedule-form .btn-confirm:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
```

- [ ] **Step 2: Add the schedule form HTML inside the modal**

In `frontend/panel.html`, find `<div class="modal-inner">` (around line 1146). Wrap the existing modal-inner content so it can be hidden, and add a sibling schedule-form div. Replace the structure:

OLD (around line 1141-1207):
```html
<div class="modal-overlay" id="modalOverlay">
  <div class="modal" id="modal">
    <div class="modal-score-bar">
      <div class="modal-score-bar-fill" id="mScoreBarFill" style="width:0%"></div>
    </div>
    <div class="modal-inner">
      ... existing modal contents ...
    </div>
  </div>
</div>
```

NEW: leave everything exactly as it is, but add an `id="modalDetailView"` to the existing `<div class="modal-inner">` (so we can toggle it), and add a sibling `<div class="schedule-form" id="scheduleForm" style="display:none;">` right after `</div>` of `modal-inner`:

```html
<div class="modal-overlay" id="modalOverlay">
  <div class="modal" id="modal">
    <div class="modal-score-bar">
      <div class="modal-score-bar-fill" id="mScoreBarFill" style="width:0%"></div>
    </div>
    <div class="modal-inner" id="modalDetailView">
      ... existing modal contents (UNCHANGED) ...
    </div>
    <div class="schedule-form" id="scheduleForm" style="display:none;">
      <h3>Agendar entrevista</h3>
      <p class="schedule-sub" id="scheduleCandidateName"></p>

      <label for="scheduleDate">Fecha y hora *</label>
      <input type="datetime-local" id="scheduleDate" />

      <label for="scheduleLocation">Lugar / link de la reunión (opcional)</label>
      <input type="text" id="scheduleLocation" placeholder="Google Meet · Zoom · Oficina CDMX" />

      <div class="schedule-form-actions">
        <button class="btn-cancel" onclick="hideScheduleForm()">Cancelar</button>
        <button class="btn-confirm" id="scheduleConfirmBtn" disabled onclick="submitSchedule()">Confirmar y enviar</button>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Replace the `showScheduleForm` stub with the real implementation**

In the `<script>` section, replace the stub `function showScheduleForm(_id, _name) { ... }` with:

```javascript
  function showScheduleForm(id, name) {
    _currentCandidateId = id;
    document.getElementById('scheduleCandidateName').textContent = name;
    document.getElementById('scheduleDate').value = '';
    document.getElementById('scheduleLocation').value = '';
    // Set min to today (in local timezone, datetime-local format)
    const now = new Date();
    const tzOffset = now.getTimezoneOffset() * 60000;
    document.getElementById('scheduleDate').min = new Date(Date.now() - tzOffset).toISOString().slice(0, 16);
    document.getElementById('scheduleConfirmBtn').disabled = true;
    document.getElementById('modalDetailView').style.display = 'none';
    document.getElementById('scheduleForm').style.display = 'block';
  }

  function hideScheduleForm() {
    document.getElementById('scheduleForm').style.display = 'none';
    document.getElementById('modalDetailView').style.display = 'block';
  }

  function submitSchedule() {
    const interview_at = document.getElementById('scheduleDate').value;
    const interview_location = document.getElementById('scheduleLocation').value.trim();
    if (!interview_at) return;
    doAction('schedule', { interview_at, interview_location: interview_location || undefined });
    // doAction calls closeModal which we override below to also reset the form view
  }

  // Enable/disable confirm button as user types
  document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('scheduleDate');
    if (dateInput) {
      dateInput.addEventListener('input', () => {
        document.getElementById('scheduleConfirmBtn').disabled = !dateInput.value;
      });
    }
  });
```

- [ ] **Step 4: Update `closeModal()` to also reset the schedule form**

Replace `closeModal()` (around line 1482):

```javascript
  function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
    // Reset to detail view in case modal was on the schedule form
    const sf = document.getElementById('scheduleForm');
    const dv = document.getElementById('modalDetailView');
    if (sf) sf.style.display = 'none';
    if (dv) dv.style.display = 'block';
  }
```

- [ ] **Step 5: Manual smoke test — Schedule**

1. Restart the server.
2. Open the panel, click a candidate, click "Agendar".
3. Verify the modal flips to the schedule form, candidate name shown.
4. Try to click "Confirmar" with empty date — should be disabled.
5. Pick a future date, click "Confirmar" → modal closes, refresh page, candidate row should reflect scheduled status (still no badge yet — that's Task 7).
6. Verify in DB: `sqlite3 cvsmart.db "SELECT name, status, interview_at, interview_location FROM candidates WHERE status='scheduled';"`
7. Click "Cancelar" instead → returns to detail view without changes.
8. Pick a past date — should be blocked client-side (input min). If user bypasses with devtools, backend should return 400.

Expected: Schedule flow works end-to-end, persists data correctly.

- [ ] **Step 6: Commit**

```bash
git add frontend/panel.html
git commit -m "feat(panel): add schedule mini-modal with datetime input"
```

---

## Task 7: Frontend — Status badges in tables + row dimming for rejected

**Files:**
- Modify: `frontend/panel.html` (CSS + replace `renderStatusBadge` stub)

- [ ] **Step 1: Add CSS for badges and rejected rows**

In `frontend/panel.html`, find the `.skill-tag` styles (around line 740). Insert these styles AFTER `.skill-tag`:

```css
    /* Status badges in candidate rows */
    .status-badge {
      display: inline-block;
      padding: 3px 9px;
      border-radius: 100px;
      font-size: 0.66rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      margin-left: 8px;
      vertical-align: middle;
      border: 1px solid;
    }

    .status-approved {
      color: #22c55e;
      background: rgba(34, 197, 94, 0.08);
      border-color: rgba(34, 197, 94, 0.3);
    }

    .status-scheduled {
      color: #eab308;
      background: rgba(234, 179, 8, 0.08);
      border-color: rgba(234, 179, 8, 0.3);
    }

    .status-rejected {
      color: #a0a0a0;
      background: rgba(160, 160, 160, 0.08);
      border-color: rgba(160, 160, 160, 0.3);
    }

    /* Rejected rows look "muted" but stay visible */
    .candidates-table tbody tr.row-rejected {
      opacity: 0.5;
    }

    .candidates-table tbody tr.row-rejected:hover {
      opacity: 0.85;
    }
```

- [ ] **Step 2: Replace `renderStatusBadge` stub with real implementation**

In the `<script>` section, replace `function renderStatusBadge(_c) { return ''; }` with:

```javascript
  function renderStatusBadge(c) {
    if (!c.status || c.status === 'pending') return '';
    if (c.status === 'approved') {
      return `<span class="status-badge status-approved">✓ Aprobado</span>`;
    }
    if (c.status === 'scheduled') {
      let title = 'Agendado';
      if (c.interview_at) {
        title = `Agendado · ${formatInterviewDateShort(c.interview_at)}`;
        if (c.interview_location) title += ` · ${c.interview_location}`;
      }
      return `<span class="status-badge status-scheduled" title="${esc(title)}">◷ Agendado</span>`;
    }
    if (c.status === 'rejected') {
      return `<span class="status-badge status-rejected">✕ Descartado</span>`;
    }
    return '';
  }

  function formatInterviewDateShort(iso) {
    // "2026-05-15T10:00" → "15 may 2026, 10:00"
    const months = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
    const dt = new Date(iso);
    if (isNaN(dt)) return iso;
    const hh = String(dt.getHours()).padStart(2, '0');
    const mm = String(dt.getMinutes()).padStart(2, '0');
    return `${dt.getDate()} ${months[dt.getMonth()]} ${dt.getFullYear()}, ${hh}:${mm}`;
  }
```

- [ ] **Step 3: Update `renderCandidatesTable2` to also include badges + rejected styling**

In `frontend/panel.html`, find `renderCandidatesTable2` (around lines 1248-1277). Replace the `return ` template with:

```javascript
      const score = parseFloat(c.score) || 0;
      const cls   = score >= 8 ? 'score-green' : score >= 6 ? 'score-yellow' : 'score-red';
      const rank  = String(i + 1).padStart(2, '0');
      const badge = renderStatusBadge(c);
      const rowCls = c.status === 'rejected' ? 'row-rejected' : '';
      return `
        <tr class="${rowCls}" onclick="openModal(${c.id})">
          <td class="col-rank">${esc(rank)}</td>
          <td class="col-name">${esc(c.name)}${badge}</td>
          <td><span class="score-badge ${cls}">${esc(c.score)}</span></td>
          <td class="col-label">${esc(c.score_label || '—')}</td>
          <td class="col-label">${esc(c.years_experience ?? '—')} años</td>
          <td class="col-avail">${esc(c.availability || '—')}</td>
          <td class="col-actions" onclick="event.stopPropagation()">
            <button class="icon-btn" title="Descargar CV" onclick="downloadCV(${c.id})">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </button>
            <button class="icon-btn" title="Ver detalles" onclick="openModal(${c.id})">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </button>
          </td>
        </tr>`;
```

- [ ] **Step 4: Manual smoke test — Badges**

1. Restart the server.
2. Open the panel.
3. You should now see badges on candidates that have been processed (approve/schedule/reject from earlier tasks).
4. Hover the "Agendado" badge → tooltip shows date + location.
5. Rejected candidate's row should be visibly dimmed (opacity 0.5).
6. Pending candidates should show no badge.
7. Switch between Dashboard and Candidatos sections → both tables show the badges.

Expected: Visual states reflect correctly, hover for scheduled shows the formatted date.

- [ ] **Step 5: Commit**

```bash
git add frontend/panel.html
git commit -m "feat(panel): add status badges and rejected row dimming"
```

---

## Task 8: Frontend — Toast notification component

**Files:**
- Modify: `frontend/panel.html` (CSS + HTML element + replace `showToast` stub)

- [ ] **Step 1: Add toast CSS**

In `frontend/panel.html`, find the closing `}` of `.row-rejected:hover` (added in Task 7) and insert AFTER it:

```css
    /* Toast notifications */
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 300;
      padding: 12px 18px;
      border-radius: 10px;
      background: #161616;
      color: #fff;
      font-size: 0.85rem;
      font-weight: 600;
      border: 1px solid rgba(255,255,255,0.08);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
      transform: translateX(140%);
      transition: transform 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
      max-width: 360px;
    }

    .toast.show { transform: translateX(0); }

    .toast.toast-success-green  { border-left: 4px solid #22c55e; }
    .toast.toast-success-yellow { border-left: 4px solid #eab308; }
    .toast.toast-success-red    { border-left: 4px solid #e43c2f; }
    .toast.toast-error          { border-left: 4px solid #f87171; background: #2a1010; }
```

- [ ] **Step 2: Add toast HTML element**

In `frontend/panel.html`, find the closing `</body>` tag (line 1494). Insert BEFORE it:

```html
<div class="toast" id="toast"></div>
```

- [ ] **Step 3: Replace `showToast` stub with real implementation**

In the `<script>` section, replace `function showToast(message, _variant) { console.log('[toast]', message); }` with:

```javascript
  let _toastTimer = null;
  function showToast(message, variant = 'success-green') {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.className = 'toast show toast-' + variant;
    if (_toastTimer) clearTimeout(_toastTimer);
    _toastTimer = setTimeout(() => {
      el.className = 'toast toast-' + variant;
    }, 4000);
  }
```

- [ ] **Step 4: Manual smoke test — Toast**

1. Restart the server.
2. Approve a candidate → green toast slides in from the right with "Candidato aprobado · Email enviado" (or "· Sin email" if SMTP isn't configured).
3. Schedule another candidate → yellow toast.
4. Reject another → red toast.
5. Each toast disappears after ~4 seconds.
6. Triggering a second action while a toast is showing replaces the message (no stacking).

Expected: Toast looks polished, animated, color-coded.

- [ ] **Step 5: Commit**

```bash
git add frontend/panel.html
git commit -m "feat(panel): add toast notifications for action feedback"
```

---

## Task 9: Frontend — Status info line in detail modal

**Files:**
- Modify: `frontend/panel.html` (HTML + JS in `openModal`)

- [ ] **Step 1: Add a status info line to the modal HTML**

In `frontend/panel.html`, find the `<div class="modal-title">` block (around lines 1149-1153):

```html
<div class="modal-title">
  <h2 id="mName"></h2>
  <p id="mEmail"></p>
</div>
```

Replace it with:

```html
<div class="modal-title">
  <h2 id="mName"></h2>
  <p id="mEmail"></p>
  <p id="mStatusInfo" style="margin-top:6px; font-size:0.78rem; font-weight:600; display:none;"></p>
</div>
```

- [ ] **Step 2: Populate the status line in `openModal()`**

In `openModal()` in `frontend/panel.html`, find the line that sets `mEmail` (around line 1452):

```javascript
document.getElementById('mEmail').textContent = c.email || 'Sin email';
```

Insert AFTER it:

```javascript
    const statusInfo = document.getElementById('mStatusInfo');
    if (c.status && c.status !== 'pending') {
      const labels = {
        approved:  { text: '✓ Aprobado',     color: '#22c55e' },
        scheduled: { text: '◷ Agendado',     color: '#eab308' },
        rejected:  { text: '✕ Descartado',   color: '#a0a0a0' },
      };
      const info = labels[c.status] || { text: c.status, color: '#a0a0a0' };
      let line = info.text;
      if (c.status === 'scheduled' && c.interview_at) {
        line += ` · ${formatInterviewDateShort(c.interview_at)}`;
        if (c.interview_location) line += ` · ${c.interview_location}`;
      }
      statusInfo.textContent = line;
      statusInfo.style.color = info.color;
      statusInfo.style.display = 'block';
    } else {
      statusInfo.style.display = 'none';
    }
```

- [ ] **Step 3: Manual smoke test — Status line in modal**

1. Restart the server.
2. Click on an "Aprobado" candidate → modal shows green "✓ Aprobado" line under the email.
3. Click on a "Agendado" candidate → modal shows yellow line "◷ Agendado · 15 may 2026, 10:00 · Google Meet".
4. Click on a "Descartado" candidate → modal shows gray "✕ Descartado".
5. Click on a pending candidate → no status line.
6. Re-approve a previously rejected candidate → toast confirms; reopen → modal now shows "Aprobado".

Expected: Recruiter can see at a glance the previous decision on any candidate.

- [ ] **Step 4: Commit**

```bash
git add frontend/panel.html
git commit -m "feat(panel): show previous decision in candidate detail modal"
```

---

## Task 10: End-to-end manual verification

**Files:** none modified — this is verification only.

- [ ] **Step 1: Run the full automated test suite**

Run: `pytest -v`
Expected: All tests pass — `test_database.py` (8 tests), `test_email_sender.py` (6 tests), `test_panel_actions.py` (9 tests).

- [ ] **Step 2: Full UI smoke test**

1. Restart the server fresh: `python -m uvicorn main:app --reload`
2. Apply with a test CV via `/aplicar` (or use existing candidates).
3. Log in to `/panel`.
4. Click each of the three buttons on different candidates and verify:
   - **Aprobar** → green toast "Candidato aprobado · Email enviado", modal closes, badge appears, status line on re-open
   - **Agendar** → schedule mini-modal, validates date, on confirm yellow toast, badge appears with hover-tooltip showing date+location, status line on re-open
   - **Descartar** → confirm dialog, red toast, candidate row dimmed to 50%, status line on re-open
5. Switch between sections (Dashboard ↔ Candidatos) — both tables show consistent state.
6. Reload the page — all states persist (badges still show).
7. Re-trigger an action on a previously processed candidate — state updates correctly (e.g. unreject by approving).
8. If `GMAIL_USER` is configured, check that real emails arrive at the candidate's address with correct copy.
9. If not configured, `email_sent` is `false` and toast shows "· Sin email".

- [ ] **Step 3: DB sanity check**

Run: `sqlite3 cvsmart.db "SELECT id, name, status, interview_at, interview_location FROM candidates WHERE status != 'pending';"`
Expected: Each row reflects the action taken in the UI.

- [ ] **Step 4: Final commit if any cleanup**

```bash
git status   # should be clean if no last-minute fixes
```

---

## Self-Review Notes (already applied)

- **Spec coverage:** sections 1 (DB), 2 (backend+email), 3 (frontend modal+actions), 4 (badges) all mapped to Tasks 1–9. Error handling cases from spec covered in Task 4 endpoint tests + Task 5 `doAction` error toast.
- **Placeholders:** none — every code block is complete and runnable.
- **Type/name consistency:** `update_candidate_status` signature matches between `database.py` (Task 2), endpoint call (Task 4), and tests. `send_action_email` signature consistent. `renderStatusBadge` stubbed in Task 5 and replaced in Task 7. `showScheduleForm`/`showToast` stubbed in Task 5, replaced in Tasks 6/8 — explicitly noted in plan.
- **Order dependency:** Task 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Tasks 1–4 are backend (each commits cleanly). Tasks 5–9 are frontend, gated by stubs that get replaced — Task 5 ships a working Aprobar/Descartar end-to-end with placeholder Schedule and console-only toast.
