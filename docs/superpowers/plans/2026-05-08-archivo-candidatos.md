# Archivo de candidatos con historial — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir al reclutador archivar candidatos para quitarlos del dashboard principal, preservando su estado original, con sección de historial y botón de restaurar.

**Architecture:** Nueva columna `archivado INTEGER DEFAULT 0` en SQLite con migración automática. El backend agrega 3 endpoints nuevos. El frontend agrega un botón de archivar por fila y una sección colapsable de historial debajo del dashboard.

**Tech Stack:** FastAPI, SQLite (sqlite3), pytest, FastAPI TestClient, HTML/CSS/JS vanilla

---

## File Map

| File | Acción | Qué cambia |
|------|--------|------------|
| `database.py` | Modify | Nueva columna `archivado`, filtro en `get_all_candidates()`, 3 funciones nuevas |
| `main.py` | Modify | 3 endpoints nuevos: archivar, desarchivar, historial |
| `frontend/panel.html` | Modify | Botón archivar en cada fila, sección historial con tabla y botón restaurar |
| `tests/test_archivo.py` | Create | Tests para las funciones de BD y los 3 endpoints |

---

## Task 1: Base de datos — columna `archivado` y funciones

**Files:**
- Modify: `database.py`
- Create: `tests/test_archivo.py`

- [ ] **Step 1: Escribir los tests que fallan**

Crear `/Users/lucianocabrera/CVSmart/tests/test_archivo.py`:

```python
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
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

```bash
cd /Users/lucianocabrera/CVSmart
pytest tests/test_archivo.py -v
```

Esperado: FAIL — `ImportError: cannot import name 'get_archived_candidates'`

- [ ] **Step 3: Implementar los cambios en `database.py`**

**3a.** Agregar `archivado` a `_NEW_COLS` (después de `notas_cita`):

```python
_NEW_COLS = [
    ("estado",       "TEXT DEFAULT 'pendiente'"),
    ("fecha_inicio", "TEXT"),
    ("fecha_cita",   "TEXT"),
    ("hora_cita",    "TEXT"),
    ("notas_cita",   "TEXT"),
    ("archivado",    "INTEGER DEFAULT 0"),
]
```

**3b.** Agregar `WHERE archivado = 0` a `get_all_candidates()`:

```python
def get_all_candidates() -> list:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT id, name, email, phone, score, score_label, years_experience,
                   education_level, matching_skills, summary, strength, weaknesses,
                   availability, expected_salary, specific_experience,
                   cv_original_name, email_sent, estado, created_at
            FROM candidates WHERE archivado = 0 ORDER BY score DESC, created_at DESC
        """).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["matching_skills"] = json.loads(d["matching_skills"] or "[]")
            d["weaknesses"] = json.loads(d["weaknesses"] or "[]")
            result.append(d)
        return result
```

**3c.** Agregar las 3 funciones nuevas al final de `database.py`:

```python
def archive_candidate(candidate_id: int) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE candidates SET archivado = 1 WHERE id = ? AND archivado = 0",
            (candidate_id,)
        )
        return cur.rowcount > 0

def unarchive_candidate(candidate_id: int) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE candidates SET archivado = 0 WHERE id = ? AND archivado = 1",
            (candidate_id,)
        )
        return cur.rowcount > 0

def get_archived_candidates() -> list:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT id, name, email, score, score_label, estado, created_at
            FROM candidates WHERE archivado = 1 ORDER BY created_at DESC
        """).fetchall()
        return [dict(row) for row in rows]
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

```bash
cd /Users/lucianocabrera/CVSmart
pytest tests/test_archivo.py -v
```

Esperado: 7 tests PASS

- [ ] **Step 5: Correr todos los tests**

```bash
pytest --tb=short
```

Esperado: todos en verde.

- [ ] **Step 6: Commit**

```bash
git add database.py tests/test_archivo.py
git commit -m "feat: add archivado column and archive/unarchive functions to database"
```

---

## Task 2: Backend — endpoints archivar, desarchivar, historial

**Files:**
- Modify: `main.py`
- Modify: `tests/test_archivo.py`

- [ ] **Step 1: Agregar tests de los endpoints al archivo existente**

Abrir `tests/test_archivo.py` y agregar al final:

```python
# ── Endpoint tests ────────────────────────────────────────────────────

@pytest.fixture
def client(tmp_db):
    from main import app
    return TestClient(app)

from fastapi.testclient import TestClient

HEADERS = {"X-Recruiter-Password": "testpass"}

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
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

```bash
cd /Users/lucianocabrera/CVSmart
pytest tests/test_archivo.py -v -k "endpoint"
```

Esperado: FAIL — `404 Not Found` (rutas no existen aún)

- [ ] **Step 3: Agregar los imports necesarios en `main.py`**

Localizar la línea de imports de database en `main.py` (cerca de la línea 5) y agregar las nuevas funciones:

```python
from database import (
    init_db, insert_candidate, get_all_candidates, get_candidate,
    update_candidate_estado, mark_email_sent,
    archive_candidate, unarchive_candidate, get_archived_candidates,
)
```

- [ ] **Step 4: Agregar los 3 endpoints en `main.py`**

Agregar después del endpoint `rechazar` (al final de la sección de acciones):

```python
@app.post("/api/candidatos/{cid}/archivar")
def candidato_archivar(cid: int, _=Depends(require_auth)):
    if not get_candidate(cid):
        raise HTTPException(404, "Candidato no encontrado")
    if not archive_candidate(cid):
        raise HTTPException(404, "Candidato no encontrado")
    return {"success": True}

@app.post("/api/candidatos/{cid}/desarchivar")
def candidato_desarchivar(cid: int, _=Depends(require_auth)):
    if not get_candidate(cid):
        raise HTTPException(404, "Candidato no encontrado")
    if not unarchive_candidate(cid):
        raise HTTPException(404, "Candidato no encontrado")
    return {"success": True}

@app.get("/api/panel/historial")
def panel_historial(_=Depends(require_auth)):
    return {"candidates": get_archived_candidates()}
```

- [ ] **Step 5: Correr todos los tests**

```bash
cd /Users/lucianocabrera/CVSmart
pytest --tb=short
```

Esperado: todos en verde.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_archivo.py
git commit -m "feat: add archivar/desarchivar/historial endpoints"
```

---

## Task 3: Frontend — botón archivar y sección historial

**Files:**
- Modify: `frontend/panel.html`

- [ ] **Step 1: Agregar botón "Archivar" en cada fila de la tabla principal**

Localizar el bloque de botones en la columna `col-actions` dentro del `candidates.map(...)` (alrededor de la línea 1583). Actualmente termina con el botón de "Ver detalles". Agregar el botón de archivar después:

```html
<button class="icon-btn" title="Archivar candidato" onclick="archivarCandidato(${c.id}, this)">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>
</button>
```

- [ ] **Step 2: Agregar la sección "Historial" al HTML del panel**

Localizar el cierre de la sección del dashboard (busca `</section>` después de la tabla principal) y agregar la sección de historial justo después:

```html
<!-- HISTORIAL -->
<section id="historialSection" style="margin-top:2rem">
  <div id="historialToggle" onclick="toggleHistorial()"
       style="display:flex;align-items:center;gap:0.5rem;cursor:pointer;padding:1rem;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;user-select:none">
    <svg id="historialChevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="transition:transform .2s"><polyline points="6 9 12 15 18 9"/></svg>
    <span style="font-weight:600;color:#e2e8f0">Historial de candidatos archivados</span>
    <span id="historialCount" style="margin-left:auto;background:rgba(255,255,255,0.08);padding:2px 10px;border-radius:20px;font-size:0.8rem;color:#9ca3af">0</span>
  </div>
  <div id="historialContent" style="display:none;margin-top:0.75rem">
    <table class="candidates-table" style="width:100%">
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Email</th>
          <th>Score</th>
          <th>Estado</th>
          <th>Fecha</th>
          <th>Acción</th>
        </tr>
      </thead>
      <tbody id="historialGrid"></tbody>
    </table>
  </div>
</section>
```

- [ ] **Step 3: Agregar las funciones JS**

Agregar antes del cierre del bloque `<script>` (antes de la última `</script>`):

```js
  async function archivarCandidato(cid, btn) {
    btn.disabled = true;
    try {
      const r = await fetch(`/api/candidatos/${cid}/archivar`, {
        method: 'POST',
        headers: { 'X-Recruiter-Password': AUTH },
      });
      if (!r.ok) { showToast('Error al archivar candidato', 'error'); btn.disabled = false; return; }
      const tr = btn.closest('tr');
      tr.style.transition = 'opacity 0.3s';
      tr.style.opacity = '0';
      setTimeout(() => { tr.remove(); loadHistorial(); }, 300);
      showToast('Candidato archivado', 'success');
    } catch { showToast('Error de conexión', 'error'); btn.disabled = false; }
  }

  async function desarchivarCandidato(cid, btn) {
    btn.disabled = true;
    try {
      const r = await fetch(`/api/candidatos/${cid}/desarchivar`, {
        method: 'POST',
        headers: { 'X-Recruiter-Password': AUTH },
      });
      if (!r.ok) { showToast('Error al restaurar candidato', 'error'); btn.disabled = false; return; }
      const tr = btn.closest('tr');
      tr.style.transition = 'opacity 0.3s';
      tr.style.opacity = '0';
      setTimeout(() => { tr.remove(); loadDashboard(); }, 300);
      showToast('Candidato restaurado', 'success');
    } catch { showToast('Error de conexión', 'error'); btn.disabled = false; }
  }

  async function loadHistorial() {
    try {
      const r = await fetch('/api/panel/historial', { headers: { 'X-Recruiter-Password': AUTH } });
      if (!r.ok) return;
      const { candidates } = await r.json();
      document.getElementById('historialCount').textContent = candidates.length;
      const grid = document.getElementById('historialGrid');
      if (!candidates.length) {
        grid.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#6b7280;padding:1.5rem">Sin candidatos archivados</td></tr>`;
        return;
      }
      grid.innerHTML = candidates.map(c => {
        const score = parseFloat(c.score) || 0;
        const cls   = score >= 8 ? 'score-green' : score >= 6 ? 'score-yellow' : 'score-red';
        const fecha = c.created_at ? c.created_at.slice(0, 10) : '—';
        return `
          <tr>
            <td>${esc(c.name)}</td>
            <td style="color:#9ca3af">${esc(c.email || '—')}</td>
            <td><span class="score-badge ${cls}">${esc(String(c.score))}</span></td>
            <td>${renderEstadoBadge(c.estado || 'pendiente')}</td>
            <td style="color:#9ca3af">${esc(fecha)}</td>
            <td onclick="event.stopPropagation()">
              <button class="icon-btn" title="Restaurar candidato" onclick="desarchivarCandidato(${c.id}, this)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.5"/></svg>
              </button>
            </td>
          </tr>`;
      }).join('');
    } catch (e) { console.error('Error cargando historial:', e); }
  }

  function toggleHistorial() {
    const content  = document.getElementById('historialContent');
    const chevron  = document.getElementById('historialChevron');
    const open     = content.style.display === 'none';
    content.style.display = open ? 'block' : 'none';
    chevron.style.transform = open ? 'rotate(180deg)' : '';
    if (open) loadHistorial();
  }
```

- [ ] **Step 4: Llamar `loadHistorial()` al cargar el panel**

Localizar la línea donde se llama `loadDashboard()` al iniciar (alrededor de la línea 1521):

```js
loadDashboard();
```

Reemplazarla por:

```js
loadDashboard();
loadHistorial();
```

- [ ] **Step 5: Verificar visualmente**

Correr el servidor:

```bash
cd /Users/lucianocabrera/CVSmart
GEMINI_MOCK=1 uvicorn main:app --reload
```

Abrir `http://localhost:8000/panel` y verificar:
- Cada fila de la tabla tiene el botón de archivar (ícono de archivo)
- Al archivar, la fila desaparece con fade-out
- La sección "Historial" aparece debajo del dashboard
- Al expandirla muestra los candidatos archivados con su estado original
- El botón "Restaurar" regresa el candidato al dashboard y recarga la tabla

- [ ] **Step 6: Correr todos los tests**

```bash
pytest --tb=short
```

Esperado: todos en verde.

- [ ] **Step 7: Commit**

```bash
git add frontend/panel.html
git commit -m "feat: add archive button and historial section to admin panel"
```
