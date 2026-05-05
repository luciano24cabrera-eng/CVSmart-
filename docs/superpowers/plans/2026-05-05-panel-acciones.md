# Panel Acciones (Aceptar / Agendar / Rechazar) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conectar los botones Aprobar / Agendar / Descartar del modal de detalle de candidatos con lógica completa: sub-modales de confirmación, actualización de BD y envío de email automático.

**Architecture:** Los 3 botones ya existen en `panel.html` dentro del modal de detalle. Al hacer clic abren un sub-modal de confirmación (inline HTML), que al confirmarse llama a un endpoint FastAPI nuevo, actualiza el campo `estado` en SQLite y despacha un email HTML al candidato vía Gmail SMTP. El resultado se refleja visualmente con un badge de estado en el modal y un toast de confirmación.

**Tech Stack:** FastAPI, SQLite (sqlite3), smtplib + email.mime (stdlib), HTML/CSS/JS vanilla, pytest + httpx (TestClient).

---

## File Map

| Archivo | Cambio |
|---------|--------|
| `database.py` | Migración de 5 columnas nuevas + `update_candidate_estado()` + `estado` en `get_all_candidates()` |
| `email_sender.py` | `send_action_email()` + 3 builders HTML (`_build_aceptado_html`, `_build_agendado_html`, `_build_rechazado_html`) + helper `_email_wrapper()` |
| `main.py` | 3 endpoints POST + 2 Pydantic models + imports actualizados |
| `frontend/panel.html` | Columna Estado en ambas tablas + 3 sub-modales + CSS + JS completo |
| `.env.example` | Nueva variable `NOMBRE_EMPRESA` |
| `tests/test_database.py` | Tests para columnas nuevas y `update_candidate_estado()` |
| `tests/test_email_acciones.py` | Nuevo — tests para los 3 builders HTML y `send_action_email()` |
| `tests/test_endpoints_acciones.py` | Nuevo — tests de integración para los 3 endpoints |

---

## Task 1: Database — migración + update_candidate_estado()

**Files:**
- Modify: `database.py`
- Modify: `tests/test_database.py`

- [ ] **Step 1: Agregar tests que fallan**

Al final de `tests/test_database.py` agrega:

```python
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
```

- [ ] **Step 2: Verificar que fallan**

```bash
cd /Users/lucianocabrera/CVSmart && python -m pytest tests/test_database.py -k "estado" -v
```

Esperado: FAILED — `ImportError: cannot import name 'update_candidate_estado'`

- [ ] **Step 3: Implementar en database.py**

Reemplaza el contenido de `database.py` con lo siguiente (agrega `_NEW_COLS`, `_migrate()`, `update_candidate_estado()` y la columna `estado` en `get_all_candidates()`):

```python
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
```

- [ ] **Step 4: Verificar que los tests pasan**

```bash
cd /Users/lucianocabrera/CVSmart && python -m pytest tests/test_database.py -v
```

Esperado: todos PASSED (incluyendo los tests anteriores)

- [ ] **Step 5: Commit**

```bash
cd /Users/lucianocabrera/CVSmart && git add database.py tests/test_database.py && git commit -m "feat: add estado columns migration and update_candidate_estado()"
```

---

## Task 2: Email — send_action_email() + 3 builders HTML

**Files:**
- Create: `tests/test_email_acciones.py`
- Modify: `email_sender.py`

- [ ] **Step 1: Crear tests que fallan**

Crea `tests/test_email_acciones.py`:

```python
import os, pytest
os.environ.setdefault("GOOGLE_API_KEY", "test")

from email_sender import (
    _build_aceptado_html,
    _build_agendado_html,
    _build_rechazado_html,
    send_action_email,
)

def test_aceptado_html_contiene_fecha_y_nombre():
    html = _build_aceptado_html("Juan Pérez", "Acme Corp", "2026-06-01")
    assert "Juan Pérez" in html
    assert "2026-06-01" in html
    assert "Acme Corp" in html

def test_agendado_html_contiene_cita():
    html = _build_agendado_html("María García", "Acme", "2026-05-20", "10:00", "Entrevista por Zoom")
    assert "2026-05-20" in html
    assert "10:00" in html
    assert "Entrevista por Zoom" in html

def test_agendado_html_omite_notas_vacias():
    html = _build_agendado_html("Ana", "Acme", "2026-05-20", "10:00", "")
    assert "📝" not in html

def test_rechazado_html_contiene_nombre_y_empresa():
    html = _build_rechazado_html("Pedro Ruiz", "TechCo")
    assert "Pedro Ruiz" in html
    assert "TechCo" in html

def test_rechazado_html_es_empatico():
    html = _build_rechazado_html("Pedro Ruiz", "TechCo")
    assert "agradecemos" in html.lower() or "agradece" in html.lower()

def test_send_action_email_sin_credenciales_retorna_false(monkeypatch):
    monkeypatch.delenv("GMAIL_USER", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    assert send_action_email("x@test.com", "Test", "aceptado", fecha_inicio="2026-06-01") is False

def test_send_action_email_accion_invalida(monkeypatch):
    monkeypatch.delenv("GMAIL_USER", raising=False)
    assert send_action_email("x@test.com", "Test", "invalida") is False

def test_html_escapa_caracteres_especiales():
    html = _build_aceptado_html('<script>alert(1)</script>', "Acme", "2026-06-01")
    assert "<script>" not in html
```

- [ ] **Step 2: Verificar que fallan**

```bash
cd /Users/lucianocabrera/CVSmart && python -m pytest tests/test_email_acciones.py -v
```

Esperado: FAILED — `ImportError: cannot import name '_build_aceptado_html'`

- [ ] **Step 3: Implementar en email_sender.py**

Reemplaza el contenido completo de `email_sender.py`:

```python
import os, smtplib
import html as _html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_BADGE = {
    "Excelente": ("#166534", "#dcfce7"),
    "Bueno":     ("#92400e", "#fef3c7"),
    "En desarrollo": ("#991b1b", "#fee2e2"),
}

_WRAPPER_STYLE = "max-width:600px;margin:32px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(31,56,100,.1)"
_HEADER_STYLE  = "background:linear-gradient(135deg,#1F3864,#2E75B6);padding:32px;text-align:center"

def _email_wrapper(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F8FAFF;font-family:Arial,sans-serif">
  <div style="{_WRAPPER_STYLE}">
    <div style="{_HEADER_STYLE}">
      <h1 style="color:#fff;margin:0;font-size:26px">🧠 CVSmart</h1>
      <p style="color:rgba(255,255,255,.8);margin:8px 0 0">Sistema inteligente de filtrado de CVs</p>
    </div>
    <div style="padding:32px">{body_html}</div>
    <div style="background:#F8FAFF;padding:16px;text-align:center;color:#9ca3af;font-size:12px">
      <p style="margin:0">Equipo CVSmart &copy; 2026 — Este correo fue generado automáticamente.</p>
    </div>
  </div>
</body>
</html>"""

def build_email_html(name: str, score_label: str, strength: str, weaknesses: list) -> str:
    color, bg = _BADGE.get(score_label, ("#374151", "#f3f4f6"))
    safe_name = _html.escape(name)
    safe_strength = _html.escape(strength)
    wk_items = "".join(f"<li style='margin-bottom:6px'>{_html.escape(w)}</li>" for w in weaknesses)
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    body = f"""
      <p style="font-size:16px">Hola <strong>{safe_name}</strong>,</p>
      <p style="color:#4b5563">Recibimos tu CV y lo analizamos con nuestra IA. Aquí está tu retroalimentación personalizada:</p>
      <div style="margin:24px 0">
        <p style="font-weight:bold;color:#1F3864;margin-bottom:8px">Tu nivel de perfil:</p>
        <span style="background:{bg};color:{color};padding:8px 20px;border-radius:20px;font-weight:bold;font-size:15px">{score_label}</span>
      </div>
      <div style="margin:24px 0">
        <p style="font-weight:bold;color:#1F3864;margin-bottom:8px">Tu principal fortaleza:</p>
        <p style="background:#F0F7FF;border-left:4px solid #2E75B6;padding:12px 16px;border-radius:0 8px 8px 0;margin:0">{safe_strength}</p>
      </div>
      <div style="margin:24px 0">
        <p style="font-weight:bold;color:#1F3864;margin-bottom:8px">Áreas de oportunidad:</p>
        <ul style="color:#4b5563;padding-left:20px">{wk_items}</ul>
      </div>
      <p style="color:#4b5563">¿Quieres un CV más profesional? Usa nuestro Creador de CV con IA:</p>
      <a href="{base_url}/crear-cv"
         style="display:block;background:linear-gradient(135deg,#1F3864,#2E75B6);color:#fff;text-decoration:none;padding:14px 32px;border-radius:12px;text-align:center;font-weight:bold;margin:16px 0">
        Crear mi CV profesional →
      </a>"""
    return _email_wrapper(body)

def _build_aceptado_html(name: str, empresa: str, fecha_inicio: str) -> str:
    safe_name    = _html.escape(name)
    safe_empresa = _html.escape(empresa)
    safe_fecha   = _html.escape(fecha_inicio)
    body = f"""
      <p style="font-size:16px">Estimado/a <strong>{safe_name}</strong>,</p>
      <p style="color:#4b5563">Nos complace informarte que has sido seleccionado/a para formar parte de nuestro equipo.</p>
      <div style="margin:24px 0;background:#F0FFF4;border-left:4px solid #22c55e;padding:16px 20px;border-radius:0 8px 8px 0;">
        <p style="margin:0;font-size:15px">📅 Tu fecha de inicio es: <strong>{safe_fecha}</strong></p>
      </div>
      <p style="color:#4b5563">En los próximos días recibirás más detalles sobre tu incorporación.</p>
      <p style="color:#4b5563">¡Bienvenido/a a bordo!</p>
      <p style="color:#4b5563;margin-top:24px">Atentamente,<br><strong>Equipo de Reclutamiento</strong><br>{safe_empresa}</p>"""
    return _email_wrapper(body)

def _build_agendado_html(name: str, empresa: str, fecha_cita: str, hora_cita: str, notas: str) -> str:
    safe_name    = _html.escape(name)
    safe_empresa = _html.escape(empresa)
    safe_fecha   = _html.escape(fecha_cita)
    safe_hora    = _html.escape(hora_cita)
    notas_line   = (
        f"<p style='margin:8px 0 0'>📝 Detalles: {_html.escape(notas)}</p>"
        if notas.strip() else ""
    )
    body = f"""
      <p style="font-size:16px">Estimado/a <strong>{safe_name}</strong>,</p>
      <p style="color:#4b5563">Hemos agendado una cita contigo para continuar con tu proceso de selección.</p>
      <div style="margin:24px 0;background:#EFF6FF;border-left:4px solid #3b82f6;padding:16px 20px;border-radius:0 8px 8px 0;">
        <p style="margin:0">📅 Fecha: <strong>{safe_fecha}</strong></p>
        <p style="margin:8px 0 0">🕐 Hora: <strong>{safe_hora}</strong></p>
        {notas_line}
      </div>
      <p style="color:#4b5563">Por favor confirma tu asistencia respondiendo este correo.</p>
      <p style="color:#4b5563;margin-top:24px">Atentamente,<br><strong>Equipo de Reclutamiento</strong><br>{safe_empresa}</p>"""
    return _email_wrapper(body)

def _build_rechazado_html(name: str, empresa: str) -> str:
    safe_name    = _html.escape(name)
    safe_empresa = _html.escape(empresa)
    body = f"""
      <p style="font-size:16px">Estimado/a <strong>{safe_name}</strong>,</p>
      <p style="color:#4b5563">Agradecemos sinceramente el tiempo y el esfuerzo que dedicaste a tu postulación en <strong>{safe_empresa}</strong>.</p>
      <p style="color:#4b5563">Luego de una cuidadosa evaluación, hemos decidido continuar el proceso con otros candidatos cuyo perfil se ajusta más a las necesidades actuales del puesto.</p>
      <p style="color:#4b5563">Esta decisión no refleja tu valor profesional. Te animamos a seguir adelante y a postularte en futuras oportunidades con nosotros.</p>
      <p style="color:#4b5563">¡Mucho éxito en tu búsqueda!</p>
      <p style="color:#4b5563;margin-top:24px">Atentamente,<br><strong>Equipo de Reclutamiento</strong><br>{safe_empresa}</p>"""
    return _email_wrapper(body)

def send_action_email(to_email: str, name: str, action: str, **kwargs) -> bool:
    empresa = os.getenv("NOMBRE_EMPRESA", "CVSmart")
    builders = {
        "aceptado": lambda: (
            f"¡Felicidades! Has sido aceptado en {empresa}",
            _build_aceptado_html(name, empresa, kwargs.get("fecha_inicio", ""))
        ),
        "agendado": lambda: (
            f"Tienes una cita agendada con {empresa}",
            _build_agendado_html(name, empresa, kwargs.get("fecha_cita", ""), kwargs.get("hora_cita", ""), kwargs.get("notas", ""))
        ),
        "rechazado": lambda: (
            f"Actualización sobre tu proceso de selección en {empresa}",
            _build_rechazado_html(name, empresa)
        ),
    }
    if action not in builders:
        return False
    subject, html = builders[action]()
    gmail_user     = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_user or not gmail_password:
        print("⚠️  Email no enviado: GMAIL_USER o GMAIL_APP_PASSWORD no configurados en .env")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_user
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        return True
    except (smtplib.SMTPException, OSError) as e:
        print(f"⚠️  Error enviando email a {to_email}: {e}")
        return False

def send_feedback_email(to_email: str, name: str, score_label: str, strength: str, weaknesses: list) -> bool:
    gmail_user     = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_user or not gmail_password:
        print("⚠️  Email no enviado: GMAIL_USER o GMAIL_APP_PASSWORD no configurados en .env")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "CVSmart — Recibimos tu CV, aquí está tu retroalimentación"
    msg["From"]    = gmail_user
    msg["To"]      = to_email
    msg.attach(MIMEText(build_email_html(name, score_label, strength, weaknesses), "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        return True
    except (smtplib.SMTPException, OSError) as e:
        print(f"⚠️  Error enviando email a {to_email}: {e}")
        return False
```

- [ ] **Step 4: Verificar que los tests pasan**

```bash
cd /Users/lucianocabrera/CVSmart && python -m pytest tests/test_email_acciones.py -v
```

Esperado: todos PASSED

- [ ] **Step 5: Commit**

```bash
cd /Users/lucianocabrera/CVSmart && git add email_sender.py tests/test_email_acciones.py && git commit -m "feat: add send_action_email with aceptado/agendado/rechazado builders"
```

---

## Task 3: Backend — 3 endpoints POST

**Files:**
- Create: `tests/test_endpoints_acciones.py`
- Modify: `main.py`

- [ ] **Step 1: Crear tests que fallan**

Crea `tests/test_endpoints_acciones.py`:

```python
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
```

- [ ] **Step 2: Verificar que fallan**

```bash
cd /Users/lucianocabrera/CVSmart && python -m pytest tests/test_endpoints_acciones.py -v
```

Esperado: FAILED — `404 Not Found` (rutas no existen todavía)

- [ ] **Step 3: Implementar los 3 endpoints en main.py**

En `main.py`, actualiza la línea de imports de `database` y agrega la import de `send_action_email`. Luego agrega los 3 endpoints y los 2 modelos Pydantic. El archivo completo queda así:

```python
import os, json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Body, Header
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from database import (
    init_db, insert_candidate, get_all_candidates, get_stats,
    get_candidate, mark_email_sent, update_candidate_estado,
)
from analyzer import analyze_cv
from email_sender import send_feedback_email, send_action_email
from cv_generator import improve_cv_with_ai, generate_cv_pdf

CVS_DIR = Path("cvs")

@asynccontextmanager
async def lifespan(app: FastAPI):
    CVS_DIR.mkdir(exist_ok=True)
    init_db()
    yield

app = FastAPI(title="CVSmart V2", lifespan=lifespan)
app.mount("/styles", StaticFiles(directory="frontend/styles"), name="styles")

# ── Auth ──────────────────────────────────────────────────────────────
def require_auth(x_recruiter_password: str = Header(None)):
    if x_recruiter_password != os.getenv("SECRET_PANEL", "cvsmart2026"):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

# ── Pydantic models ───────────────────────────────────────────────────
class AceptarBody(BaseModel):
    fecha_inicio: str

class AgendarBody(BaseModel):
    fecha_cita: str
    hora_cita: str
    notas: Optional[str] = ""

# ── Candidatos ────────────────────────────────────────────────────────
@app.post("/api/aplicar")
async def aplicar(
    cv: UploadFile = File(...),
    email: str = Form(...),
    phone: str = Form(""),
    availability: str = Form(...),
    expected_salary: str = Form(...),
    specific_experience: str = Form(...),
):
    if cv.content_type != "application/pdf":
        raise HTTPException(400, "Solo se aceptan archivos PDF")
    pdf_bytes = await cv.read()
    try:
        analysis = analyze_cv(pdf_bytes)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(503, f"Error al analizar CV: {e}")
    filename = f"cv-{uuid.uuid4().hex}-{cv.filename}"
    (CVS_DIR / filename).write_bytes(pdf_bytes)
    cid = insert_candidate(
        name=analysis.get("nombre", "Sin nombre"),
        email=email, phone=phone,
        cv_filename=filename, cv_original_name=cv.filename,
        score=analysis.get("puntaje", 5),
        score_label=analysis.get("score_label", "Bueno"),
        years_experience=analysis.get("años_experiencia", 0),
        education_level=analysis.get("nivel_estudios", ""),
        matching_skills=json.dumps(analysis.get("habilidades_coincidentes", [])),
        summary=analysis.get("resumen", ""),
        strength=analysis.get("fortaleza", ""),
        weaknesses=json.dumps(analysis.get("debilidades", [])),
        full_analysis=json.dumps(analysis),
        availability=availability,
        expected_salary=expected_salary,
        specific_experience=specific_experience,
    )
    if email:
        sent = send_feedback_email(
            to_email=email,
            name=analysis.get("nombre", "Candidato"),
            score_label=analysis.get("score_label", "Bueno"),
            strength=analysis.get("fortaleza", ""),
            weaknesses=analysis.get("debilidades", []),
        )
        if sent:
            mark_email_sent(cid)
    return {
        "success": True,
        "candidateId": cid,
        "name": analysis.get("nombre", "Sin nombre"),
        "message": "Tu postulación fue recibida. Recibirás un correo con retroalimentación.",
    }

# ── Panel reclutador ──────────────────────────────────────────────────
@app.get("/api/panel/candidatos")
def panel_candidatos(_=Depends(require_auth)):
    return {"candidates": get_all_candidates()}

@app.get("/api/panel/stats")
def panel_stats(_=Depends(require_auth)):
    return get_stats()

@app.get("/api/panel/candidatos/{cid}")
def panel_detail(cid: int, _=Depends(require_auth)):
    c = get_candidate(cid)
    if not c:
        raise HTTPException(404, "Candidato no encontrado")
    return c

@app.get("/api/panel/candidatos/{cid}/cv")
def panel_cv(cid: int, _=Depends(require_auth)):
    c = get_candidate(cid)
    if not c:
        raise HTTPException(404, "Candidato no encontrado")
    path = CVS_DIR / c["cv_filename"]
    if not path.exists():
        raise HTTPException(404, "Archivo no encontrado")
    return FileResponse(path, filename=c.get("cv_original_name", "cv.pdf"))

# ── Acciones sobre candidatos ─────────────────────────────────────────
@app.post("/api/candidatos/{cid}/aceptar")
def candidato_aceptar(cid: int, body: AceptarBody, _=Depends(require_auth)):
    c = get_candidate(cid)
    if not c:
        raise HTTPException(404, "Candidato no encontrado")
    update_candidate_estado(cid, "aceptado", fecha_inicio=body.fecha_inicio)
    sent, warning = False, None
    if c.get("email"):
        sent = send_action_email(c["email"], c["name"], "aceptado", fecha_inicio=body.fecha_inicio)
        if not sent:
            warning = "Estado actualizado pero el correo no pudo enviarse"
    return {"success": True, "email_sent": sent, "warning": warning}

@app.post("/api/candidatos/{cid}/agendar")
def candidato_agendar(cid: int, body: AgendarBody, _=Depends(require_auth)):
    c = get_candidate(cid)
    if not c:
        raise HTTPException(404, "Candidato no encontrado")
    update_candidate_estado(
        cid, "agendado",
        fecha_cita=body.fecha_cita, hora_cita=body.hora_cita,
        notas_cita=body.notas or ""
    )
    sent, warning = False, None
    if c.get("email"):
        sent = send_action_email(
            c["email"], c["name"], "agendado",
            fecha_cita=body.fecha_cita, hora_cita=body.hora_cita, notas=body.notas or ""
        )
        if not sent:
            warning = "Estado actualizado pero el correo no pudo enviarse"
    return {"success": True, "email_sent": sent, "warning": warning}

@app.post("/api/candidatos/{cid}/rechazar")
def candidato_rechazar(cid: int, _=Depends(require_auth)):
    c = get_candidate(cid)
    if not c:
        raise HTTPException(404, "Candidato no encontrado")
    update_candidate_estado(cid, "rechazado")
    sent, warning = False, None
    if c.get("email"):
        sent = send_action_email(c["email"], c["name"], "rechazado")
        if not sent:
            warning = "Estado actualizado pero el correo no pudo enviarse"
    return {"success": True, "email_sent": sent, "warning": warning}

# ── Generador de CV ───────────────────────────────────────────────────
@app.post("/api/generar-cv")
async def generar_cv(cv_data: dict = Body(...)):
    try:
        improved = improve_cv_with_ai(cv_data)
        pdf_bytes = generate_cv_pdf(improved)
    except Exception as e:
        raise HTTPException(503, f"Error al generar CV: {e}")
    name = improved.get("nombre", "CV").replace(" ", "_")
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="CV-{name}.pdf"'},
    )

# ── Páginas HTML ──────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def serve_index(): return FileResponse("frontend/index.html")

@app.get("/aplicar", include_in_schema=False)
@app.get("/aplicar.html", include_in_schema=False)
def serve_aplicar(): return FileResponse("frontend/aplicar.html")

@app.get("/panel", include_in_schema=False)
@app.get("/panel.html", include_in_schema=False)
def serve_panel(): return FileResponse("frontend/panel.html")

@app.get("/crear-cv", include_in_schema=False)
@app.get("/crear-cv.html", include_in_schema=False)
def serve_crear_cv(): return FileResponse("frontend/crear-cv.html")
```

- [ ] **Step 4: Verificar que los tests pasan**

```bash
cd /Users/lucianocabrera/CVSmart && python -m pytest tests/test_endpoints_acciones.py -v
```

Esperado: todos PASSED

- [ ] **Step 5: Correr toda la suite para no haber roto nada**

```bash
cd /Users/lucianocabrera/CVSmart && python -m pytest tests/ -v
```

Esperado: todos PASSED

- [ ] **Step 6: Commit**

```bash
cd /Users/lucianocabrera/CVSmart && git add main.py tests/test_endpoints_acciones.py && git commit -m "feat: add aceptar/agendar/rechazar endpoints with email dispatch"
```

---

## Task 4: Frontend — Columna Estado en tablas + CSS badges

**Files:**
- Modify: `frontend/panel.html`

- [ ] **Step 1: Agregar CSS de badges de estado y toast**

Dentro del bloque `<style>` existente de `panel.html`, justo antes del cierre `</style>`, agrega:

```css
    /* ── Estado badges ─────────────────────────────────────────────── */
    .estado-badge {
      display: inline-block;
      padding: 3px 9px;
      border-radius: 100px;
      font-size: 0.68rem;
      font-weight: 600;
      letter-spacing: 0.03em;
      white-space: nowrap;
    }
    .estado-pendiente  { background: rgba(160,160,160,0.1); color: #6b7280; }
    .estado-aceptado   { background: rgba(34,197,94,0.1);   color: #22c55e; }
    .estado-agendado   { background: rgba(59,130,246,0.1);  color: #60a5fa; }
    .estado-rechazado  { background: rgba(228,60,47,0.08);  color: #f87171; }

    /* ── Toast ─────────────────────────────────────────────────────── */
    .toast {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      background: #1e1e1e;
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px;
      padding: 12px 18px;
      font-size: 0.83rem;
      color: #fff;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
      z-index: 400;
      max-width: 320px;
      animation: slideInRight 0.25s ease;
    }
    .toast.success { border-left: 3px solid #22c55e; }
    .toast.warning { border-left: 3px solid #eab308; }
    .toast.error   { border-left: 3px solid #e43c2f; }
    @keyframes slideInRight {
      from { opacity: 0; transform: translateX(16px); }
      to   { opacity: 1; transform: translateX(0); }
    }

    /* ── Sub-modales ───────────────────────────────────────────────── */
    .submodal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.85);
      backdrop-filter: blur(4px);
      -webkit-backdrop-filter: blur(4px);
      z-index: 300;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }
    .submodal-overlay.open { display: flex; }
    .submodal {
      background: #1a1a1a;
      border: 1px solid rgba(228,60,47,0.15);
      border-radius: 14px;
      padding: 1.75rem;
      width: 100%;
      max-width: 420px;
      display: flex;
      flex-direction: column;
      gap: 0.875rem;
    }
    .submodal h3 {
      font-family: 'Poppins', sans-serif;
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin: 0;
    }
    .submodal-cand-name {
      color: #a0a0a0;
      font-size: 0.85rem;
      margin: 0;
    }
    .submodal-label {
      display: block;
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #a0a0a0;
      margin-bottom: 5px;
    }
    .submodal-required { color: #e43c2f; }
    .submodal input[type="date"],
    .submodal input[type="time"],
    .submodal textarea {
      width: 100%;
      padding: 10px 12px;
      background: #111;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 8px;
      color: #fff;
      font-size: 0.88rem;
      font-family: inherit;
      transition: border-color 0.2s, box-shadow 0.2s;
      box-sizing: border-box;
    }
    .submodal input:focus,
    .submodal textarea:focus {
      outline: none;
      border-color: #e43c2f;
      box-shadow: 0 0 0 3px rgba(228,60,47,0.1);
    }
    .submodal textarea { resize: vertical; min-height: 78px; }
    .submodal-warning-text {
      color: #a0a0a0;
      font-size: 0.85rem;
      background: rgba(228,60,47,0.05);
      border: 1px solid rgba(228,60,47,0.12);
      border-radius: 8px;
      padding: 12px 14px;
      margin: 0;
      line-height: 1.5;
    }
    .submodal-actions { display: flex; gap: 8px; margin-top: 0.25rem; }
    .btn-sm-cancel {
      flex: 1; padding: 10px;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 8px; background: transparent;
      color: #a0a0a0; cursor: pointer;
      font-size: 0.83rem; font-weight: 600; font-family: inherit;
      transition: all 0.2s;
    }
    .btn-sm-cancel:hover { border-color: rgba(255,255,255,0.2); color: #fff; }
    .btn-sm-confirm {
      flex: 2; padding: 10px; border: none; border-radius: 8px;
      cursor: pointer; font-size: 0.83rem; font-weight: 700;
      font-family: inherit; color: #fff; transition: all 0.2s;
    }
    .btn-sm-green { background: #16a34a; }
    .btn-sm-green:hover { background: #15803d; box-shadow: 0 4px 12px rgba(34,197,94,0.25); }
    .btn-sm-blue  { background: #2563eb; }
    .btn-sm-blue:hover  { background: #1d4ed8; box-shadow: 0 4px 12px rgba(59,130,246,0.25); }
    .btn-sm-red   { background: #dc2626; }
    .btn-sm-red:hover   { background: #b91c1c; box-shadow: 0 4px 12px rgba(220,38,38,0.25); }
```

- [ ] **Step 2: Agregar columna Estado al `<thead>` de ambas tablas**

En `panel.html` hay dos `<thead>` idénticos (uno en `#candidatesGrid`, otro en `#candidatesGrid2`). En **ambos**, agrega `<th class="col-estado">Estado</th>` justo antes de `<th class="col-actions">Acciones</th>`:

```html
<!-- ANTES (en ambos thead): -->
              <th class="col-avail">Disponibilidad</th>
              <th class="col-actions">Acciones</th>

<!-- DESPUÉS: -->
              <th class="col-avail">Disponibilidad</th>
              <th class="col-estado">Estado</th>
              <th class="col-actions">Acciones</th>
```

- [ ] **Step 3: Agregar helper `renderEstadoBadge` en el bloque `<script>`**

Al inicio del bloque `<script>` existente (después de `let AUTH = '';`), agrega:

```javascript
  function renderEstadoBadge(estado) {
    const labels = { pendiente: 'Pendiente', aceptado: 'Aceptado', agendado: 'Agendado', rechazado: 'Rechazado' };
    const label = labels[estado] || estado;
    return `<span class="estado-badge estado-${esc(estado)}">${esc(label)}</span>`;
  }
```

- [ ] **Step 4: Actualizar el renderer de `candidatesGrid` (dashboard principal)**

En la función `loadDashboard()`, reemplaza el template string del `<tr>` (línea ~1400 aprox) para agregar la celda `col-estado` y el atributo `data-cid`:

```javascript
        return `
          <tr data-cid="${c.id}" onclick="openModal(${c.id})">
            <td class="col-rank">${esc(rankNum)}</td>
            <td class="col-name">${esc(c.name)}</td>
            <td><span class="score-badge ${cls}">${esc(c.score)}</span></td>
            <td class="col-label">${esc(c.score_label || '—')}</td>
            <td class="col-label">${esc(c.years_experience ?? '—')} años</td>
            <td class="col-avail">${esc(c.availability || '—')}</td>
            <td class="col-estado">${renderEstadoBadge(c.estado || 'pendiente')}</td>
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

- [ ] **Step 5: Actualizar `renderCandidatesTable2` (sección Candidatos)**

En la función `renderCandidatesTable2()`, reemplaza el template string del `<tr>` de igual forma:

```javascript
      return `
        <tr data-cid="${c.id}" onclick="openModal(${c.id})">
          <td class="col-rank">${esc(rank)}</td>
          <td class="col-name">${esc(c.name)}</td>
          <td><span class="score-badge ${cls}">${esc(c.score)}</span></td>
          <td class="col-label">${esc(c.score_label || '—')}</td>
          <td class="col-label">${esc(c.years_experience ?? '—')} años</td>
          <td class="col-avail">${esc(c.availability || '—')}</td>
          <td class="col-estado">${renderEstadoBadge(c.estado || 'pendiente')}</td>
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

- [ ] **Step 6: Commit**

```bash
cd /Users/lucianocabrera/CVSmart && git add frontend/panel.html && git commit -m "feat: add estado column to candidates tables"
```

---

## Task 5: Frontend — Sub-modales + JS completo + wiring

**Files:**
- Modify: `frontend/panel.html`

- [ ] **Step 1: Agregar el HTML de los 3 sub-modales**

Justo antes del cierre `</body>` (después del `<!-- MODAL -->` existente), agrega:

```html
<!-- SUB-MODAL ACEPTAR -->
<div class="submodal-overlay" id="submodalAceptar">
  <div class="submodal">
    <h3>Aceptar candidato</h3>
    <p class="submodal-cand-name" id="smAceptarName"></p>
    <div>
      <label class="submodal-label" for="smFechaInicio">Fecha de inicio <span class="submodal-required">*</span></label>
      <input type="date" id="smFechaInicio" />
    </div>
    <div class="submodal-actions">
      <button class="btn-sm-cancel" onclick="closeSubModal('aceptar')">Cancelar</button>
      <button class="btn-sm-confirm btn-sm-green" onclick="confirmAceptar()">Confirmar aceptación</button>
    </div>
  </div>
</div>

<!-- SUB-MODAL AGENDAR -->
<div class="submodal-overlay" id="submodalAgendar">
  <div class="submodal">
    <h3>Agendar cita</h3>
    <p class="submodal-cand-name" id="smAgendarName"></p>
    <div>
      <label class="submodal-label" for="smFechaCita">Fecha de la cita <span class="submodal-required">*</span></label>
      <input type="date" id="smFechaCita" />
    </div>
    <div>
      <label class="submodal-label" for="smHoraCita">Hora de la cita <span class="submodal-required">*</span></label>
      <input type="time" id="smHoraCita" />
    </div>
    <div>
      <label class="submodal-label" for="smNotas">Notas adicionales</label>
      <textarea id="smNotas" placeholder="Ej. La entrevista será por videollamada, enlace: ..."></textarea>
    </div>
    <div class="submodal-actions">
      <button class="btn-sm-cancel" onclick="closeSubModal('agendar')">Cancelar</button>
      <button class="btn-sm-confirm btn-sm-blue" onclick="confirmAgendar()">Confirmar cita</button>
    </div>
  </div>
</div>

<!-- SUB-MODAL RECHAZAR -->
<div class="submodal-overlay" id="submodalRechazar">
  <div class="submodal">
    <h3>Rechazar candidato</h3>
    <p class="submodal-cand-name" id="smRechazarName"></p>
    <p class="submodal-warning-text">¿Estás seguro de que deseas rechazar a este candidato? Se le enviará un correo de notificación.</p>
    <div class="submodal-actions">
      <button class="btn-sm-cancel" onclick="closeSubModal('rechazar')">Cancelar</button>
      <button class="btn-sm-confirm btn-sm-red" onclick="confirmRechazar()">Confirmar rechazo</button>
    </div>
  </div>
</div>
```

- [ ] **Step 2: Agregar badge de estado en el header del modal de detalle**

En el bloque `<div class="modal-title">`, agrega `<p id="mEstadoBadge"></p>` debajo de `<p id="mEmail"></p>`:

```html
<!-- ANTES: -->
        <div class="modal-title">
          <h2 id="mName"></h2>
          <p id="mEmail"></p>
        </div>

<!-- DESPUÉS: -->
        <div class="modal-title">
          <h2 id="mName"></h2>
          <p id="mEmail"></p>
          <p id="mEstadoBadge" style="margin-top:6px"></p>
        </div>
```

- [ ] **Step 3: Agregar variables de estado global y función updateActionButtons**

Al inicio del `<script>`, justo después de `let _cachedStats = {};`, agrega:

```javascript
  let _currentCandidateId = null;
  let _currentCandidateName = '';

  function updateActionButtons(estado) {
    const isActioned = estado !== 'pendiente';
    ['.action-approve', '.action-schedule', '.action-discard'].forEach(sel => {
      const btn = document.querySelector(sel);
      if (!btn) return;
      btn.disabled = isActioned;
      btn.style.opacity = isActioned ? '0.35' : '1';
      btn.style.cursor  = isActioned ? 'not-allowed' : 'pointer';
    });
  }
```

- [ ] **Step 4: Agregar JS de sub-modales, toast y _postAction**

Justo antes del cierre `</script>`, agrega:

```javascript
  // ── Sub-modales ────────────────────────────────────────────────────
  function openSubModal(action) {
    if (action === 'aceptar') {
      document.getElementById('smAceptarName').textContent = _currentCandidateName;
      document.getElementById('smFechaInicio').value = '';
      document.getElementById('submodalAceptar').classList.add('open');
    } else if (action === 'agendar') {
      document.getElementById('smAgendarName').textContent = _currentCandidateName;
      document.getElementById('smFechaCita').value = '';
      document.getElementById('smHoraCita').value = '';
      document.getElementById('smNotas').value = '';
      document.getElementById('submodalAgendar').classList.add('open');
    } else if (action === 'rechazar') {
      document.getElementById('smRechazarName').textContent = _currentCandidateName;
      document.getElementById('submodalRechazar').classList.add('open');
    }
  }

  function closeSubModal(action) {
    const ids = { aceptar: 'submodalAceptar', agendar: 'submodalAgendar', rechazar: 'submodalRechazar' };
    document.getElementById(ids[action]).classList.remove('open');
  }

  // ── Toast ──────────────────────────────────────────────────────────
  function showToast(msg, type = 'success') {
    const prev = document.getElementById('_toast');
    if (prev) prev.remove();
    const el = document.createElement('div');
    el.id = '_toast';
    el.className = `toast ${type}`;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }

  // ── Post-acción ────────────────────────────────────────────────────
  function _postAction(newEstado) {
    updateActionButtons(newEstado);
    document.getElementById('mEstadoBadge').innerHTML = renderEstadoBadge(newEstado);
    const idx = _cachedCandidates.findIndex(c => c.id === _currentCandidateId);
    if (idx >= 0) _cachedCandidates[idx].estado = newEstado;
    document.querySelectorAll(`tr[data-cid="${_currentCandidateId}"] .col-estado`).forEach(cell => {
      cell.innerHTML = renderEstadoBadge(newEstado);
    });
  }

  // ── Confirmaciones ─────────────────────────────────────────────────
  async function confirmAceptar() {
    const fecha = document.getElementById('smFechaInicio').value;
    if (!fecha) { document.getElementById('smFechaInicio').focus(); return; }
    closeSubModal('aceptar');
    const r = await fetch(`/api/candidatos/${_currentCandidateId}/aceptar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Recruiter-Password': AUTH },
      body: JSON.stringify({ fecha_inicio: fecha })
    });
    const data = await r.json();
    if (!r.ok) { showToast('Error al procesar la acción', 'error'); return; }
    _postAction('aceptado');
    showToast(data.email_sent ? '✓ Candidato aceptado. Correo enviado.' : '✓ Estado actualizado. Correo no enviado.', data.email_sent ? 'success' : 'warning');
  }

  async function confirmAgendar() {
    const fecha = document.getElementById('smFechaCita').value;
    const hora  = document.getElementById('smHoraCita').value;
    if (!fecha) { document.getElementById('smFechaCita').focus(); return; }
    if (!hora)  { document.getElementById('smHoraCita').focus();  return; }
    const notas = document.getElementById('smNotas').value;
    closeSubModal('agendar');
    const r = await fetch(`/api/candidatos/${_currentCandidateId}/agendar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Recruiter-Password': AUTH },
      body: JSON.stringify({ fecha_cita: fecha, hora_cita: hora, notas })
    });
    const data = await r.json();
    if (!r.ok) { showToast('Error al procesar la acción', 'error'); return; }
    _postAction('agendado');
    showToast(data.email_sent ? '✓ Cita agendada. Correo enviado.' : '✓ Estado actualizado. Correo no enviado.', data.email_sent ? 'success' : 'warning');
  }

  async function confirmRechazar() {
    closeSubModal('rechazar');
    const r = await fetch(`/api/candidatos/${_currentCandidateId}/rechazar`, {
      method: 'POST',
      headers: { 'X-Recruiter-Password': AUTH }
    });
    const data = await r.json();
    if (!r.ok) { showToast('Error al procesar la acción', 'error'); return; }
    _postAction('rechazado');
    showToast(data.email_sent ? '✓ Candidato rechazado. Correo enviado.' : '✓ Estado actualizado. Correo no enviado.', data.email_sent ? 'success' : 'warning');
  }

  // Cerrar sub-modales al hacer clic fuera
  ['submodalAceptar', 'submodalAgendar', 'submodalRechazar'].forEach(id => {
    document.getElementById(id).addEventListener('click', e => {
      if (e.target.id === id) e.target.classList.remove('open');
    });
  });
```

- [ ] **Step 5: Actualizar openModal() para conectar botones y mostrar estado**

En la función `openModal(id)` existente, reemplaza el cuerpo completo por:

```javascript
  async function openModal(id) {
    const res = await fetch(`/api/panel/candidatos/${id}`, { headers: { 'X-Recruiter-Password': AUTH } });
    const c   = await res.json();

    _currentCandidateId   = id;
    _currentCandidateName = c.name;

    const initials = c.name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
    const score    = parseFloat(c.score) || 0;
    const pct      = Math.min(score / 10, 1);
    const circ     = 251.3;
    const filled   = pct * circ;
    const ringColor = score >= 8 ? '#22c55e' : score >= 6 ? '#eab308' : '#e43c2f';

    document.getElementById('mAvatar').textContent      = initials;
    document.getElementById('mName').textContent        = c.name;
    document.getElementById('mEmail').textContent       = c.email || 'Sin email';
    document.getElementById('mEstadoBadge').innerHTML   = renderEstadoBadge(c.estado || 'pendiente');
    document.getElementById('mSummary').textContent     = c.summary || '—';
    document.getElementById('mStrength').textContent    = c.strength || '—';
    document.getElementById('mScoreBarFill').style.width = (pct * 100) + '%';

    document.getElementById('mScoreRing').innerHTML = `
      <svg width="72" height="72" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="7"/>
        <circle cx="50" cy="50" r="40" fill="none" stroke="${ringColor}" stroke-width="7"
          stroke-dasharray="${filled} ${circ}" stroke-linecap="round"
          transform="rotate(-90 50 50)" style="transition:stroke-dasharray 0.6s ease"/>
        <text x="50" y="50" text-anchor="middle" dominant-baseline="central"
          font-size="22" font-weight="800" fill="white" font-family="Poppins,sans-serif">${c.score}</text>
      </svg>`;

    const wk = document.getElementById('mWeaknesses');
    wk.innerHTML = (c.weaknesses || []).map(w => `<li>${esc(w)}</li>`).join('') || '<li>—</li>';

    const sk = document.getElementById('mSkills');
    sk.innerHTML = (c.matching_skills || []).map(s => `<span class="skill-tag">${esc(s)}</span>`).join('') || '<span style="color:#a0a0a0">—</span>';

    document.getElementById('mAnswers').innerHTML = `
      <div class="answer-row"><span>Disponibilidad</span><span>${esc(c.availability || '—')}</span></div>
      <div class="answer-row"><span>Sueldo esperado</span><span>${esc(c.expected_salary || '—')}</span></div>
      <div class="answer-row"><span>Años de experiencia</span><span>${esc(c.specific_experience || '—')}</span></div>`;

    document.getElementById('mDownloadBtn').onclick = () => downloadCV(id);

    // Wire action buttons
    const estado = c.estado || 'pendiente';
    updateActionButtons(estado);
    if (estado === 'pendiente') {
      document.querySelector('.action-approve').onclick  = () => openSubModal('aceptar');
      document.querySelector('.action-schedule').onclick = () => openSubModal('agendar');
      document.querySelector('.action-discard').onclick  = () => openSubModal('rechazar');
    }

    document.getElementById('modalOverlay').classList.add('open');
  }
```

- [ ] **Step 6: Actualizar el manejador de Escape para cerrar también los sub-modales**

Reemplaza el listener de `keydown` existente:

```javascript
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.submodal-overlay.open').forEach(o => o.classList.remove('open'));
      closeModal();
    }
  });
```

- [ ] **Step 7: Prueba manual**

```bash
cd /Users/lucianocabrera/CVSmart && uvicorn main:app --reload --port 8000
```

Abre http://localhost:8000/panel, inicia sesión con la contraseña del `.env` y verifica:

1. La tabla muestra la columna Estado con badge "Pendiente" en gris para todos los candidatos.
2. Clic en cualquier candidato → modal de detalle → badge de estado en el header → botones activos.
3. Clic en "✓ Aprobar" → sub-modal con date picker → ingresar fecha → "Confirmar aceptación" → modal se cierra, badge cambia a verde "Aceptado", botones se deshabilitan, toast aparece.
4. Abre el mismo candidato de nuevo → botones deshabilitados, badge muestra "Aceptado".
5. Repetir flujo para Agendar (con fecha + hora + notas) y Rechazar.
6. Verificar que la columna Estado en la tabla se actualiza sin recargar la página.

- [ ] **Step 8: Commit**

```bash
cd /Users/lucianocabrera/CVSmart && git add frontend/panel.html && git commit -m "feat: add action sub-modals, toast, and status badge wiring to panel"
```

---

## Task 6: .env.example + suite completa

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Agregar NOMBRE_EMPRESA al .env.example**

Reemplaza el contenido de `.env.example`:

```
GOOGLE_API_KEY=tu_clave_aqui
SECRET_PANEL=cvsmart2026
GMAIL_USER=tu_correo@gmail.com
GMAIL_APP_PASSWORD=tu_app_password_aqui
GOOGLE_MODEL=gemini-flash-latest
NOMBRE_EMPRESA=CVSmart
```

- [ ] **Step 2: Correr la suite completa**

```bash
cd /Users/lucianocabrera/CVSmart && python -m pytest tests/ -v
```

Esperado: todos PASSED — `test_database.py`, `test_email_acciones.py`, `test_endpoints_acciones.py`

- [ ] **Step 3: Commit final**

```bash
cd /Users/lucianocabrera/CVSmart && git add .env.example && git commit -m "chore: add NOMBRE_EMPRESA to .env.example"
```

---

## Prueba rápida con curl (post-implementación)

```bash
# Verificar que el servidor está corriendo
curl -s http://localhost:8000/api/panel/stats -H "X-Recruiter-Password: cvsmart2026"

# Aceptar candidato ID 1
curl -X POST http://localhost:8000/api/candidatos/1/aceptar \
  -H "X-Recruiter-Password: cvsmart2026" \
  -H "Content-Type: application/json" \
  -d '{"fecha_inicio": "2026-06-01"}'
# Esperado: {"success":true,"email_sent":true,"warning":null}

# Agendar candidato ID 2
curl -X POST http://localhost:8000/api/candidatos/2/agendar \
  -H "X-Recruiter-Password: cvsmart2026" \
  -H "Content-Type: application/json" \
  -d '{"fecha_cita": "2026-05-15", "hora_cita": "10:00", "notas": "Entrevista por Zoom"}'
# Esperado: {"success":true,"email_sent":true,"warning":null}

# Rechazar candidato ID 3
curl -X POST http://localhost:8000/api/candidatos/3/rechazar \
  -H "X-Recruiter-Password: cvsmart2026"
# Esperado: {"success":true,"email_sent":true,"warning":null}
```
