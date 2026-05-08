# Confirmación post-envío con resultados del análisis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar al candidato su score, fortaleza principal y áreas de mejora inmediatamente después de enviar su CV.

**Architecture:** El backend extiende el response de `/api/aplicar` con los datos del análisis. El frontend reemplaza el `successState` estático con una tarjeta dinámica que inyecta esos datos via JS.

**Tech Stack:** FastAPI (Python), HTML/CSS/JS vanilla, pytest, FastAPI TestClient

---

## File Map

| File | Acción | Qué cambia |
|------|--------|------------|
| `main.py` | Modify | Agregar `score_label`, `score`, `fortaleza`, `debilidades`, `resumen` al return del endpoint `/api/aplicar` |
| `tests/test_aplicar_response.py` | Create | Test que verifica los nuevos campos en el response |
| `frontend/aplicar.html` | Modify | Reemplazar HTML del `successState`, agregar CSS del badge, actualizar JS para inyectar datos |

---

## Task 1: Extender el response del backend

**Files:**
- Modify: `main.py:123-128`
- Create: `tests/test_aplicar_response.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_aplicar_response.py`:

```python
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
```

- [ ] **Step 2: Correr el test para verificar que falla**

```bash
cd /Users/lucianocabrera/CVSmart
pytest tests/test_aplicar_response.py -v
```

Esperado: FAIL — `AssertionError: 'score_label' not in {...}`

- [ ] **Step 3: Implementar el cambio en `main.py`**

Reemplazar el bloque `return` al final del endpoint `POST /api/aplicar` (línea 123):

```python
    return {
        "success": True,
        "candidateId": cid,
        "name": analysis.get("nombre", "Sin nombre"),
        "score_label": analysis.get("score_label", "Bueno"),
        "score": analysis.get("puntaje", 5),
        "fortaleza": analysis.get("fortaleza", ""),
        "debilidades": analysis.get("debilidades", []),
        "resumen": analysis.get("resumen", ""),
        "message": "Tu postulación fue recibida. Recibirás un correo con retroalimentación.",
    }
```

- [ ] **Step 4: Correr el test para verificar que pasa**

```bash
pytest tests/test_aplicar_response.py -v
```

Esperado: PASS — `test_aplicar_retorna_campos_de_analisis PASSED`

- [ ] **Step 5: Correr todos los tests para verificar que no se rompió nada**

```bash
pytest --tb=short
```

Esperado: todos en verde.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_aplicar_response.py
git commit -m "feat: include analysis fields in /api/aplicar response"
```

---

## Task 2: Rediseñar el successState en el frontend

**Files:**
- Modify: `frontend/aplicar.html` (líneas ~252-280 CSS, ~412-421 HTML, ~503-504 JS)

- [ ] **Step 1: Reemplazar el HTML del `successState`**

Ubicar el bloque entre líneas 412-421 y reemplazarlo por:

```html
    <!-- SUCCESS -->
    <div class="success" id="successState" style="display:none">
      <div class="success-icon">🎉</div>
      <h2>¡Postulación recibida, <span id="resName"></span>!</h2>
      <p style="color:#6b7280;margin-bottom:1.5rem">Tu CV fue analizado exitosamente.<br>
         <strong>Revisa tu correo</strong> — te enviamos retroalimentación completa.</p>

      <div style="margin-bottom:1.5rem">
        <p style="font-size:0.85rem;color:#6b7280;margin-bottom:0.5rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em">Tu nivel de perfil</p>
        <span id="resBadge" class="score-badge"></span>
      </div>

      <div style="background:#F0F7FF;border-left:4px solid var(--color-primary);border-radius:0 10px 10px 0;padding:1rem 1.25rem;margin-bottom:1.5rem;text-align:left">
        <p style="font-size:0.85rem;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:0.4rem">Tu fortaleza principal</p>
        <p id="resFortaleza" style="margin:0;color:#1F3864;font-weight:500"></p>
      </div>

      <div style="text-align:left;margin-bottom:1.75rem">
        <p style="font-size:0.85rem;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:0.6rem">Áreas de oportunidad</p>
        <ul id="resDebilidades" style="padding-left:1.2rem;color:#4b5563;margin:0"></ul>
      </div>

      <div style="display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;">
        <a href="/" class="btn-back">← Volver al inicio</a>
        <a href="/crear-cv" style="display:inline-block;padding:12px 28px;background-color:var(--color-accent);color:#fff;border-radius:10px;text-decoration:none;font-weight:600;">Mejorar mi CV →</a>
      </div>
    </div>
```

- [ ] **Step 2: Agregar CSS del badge de score**

Dentro del bloque `<style>` del archivo, agregar después de la regla `.btn-back:hover { ... }`:

```css
    .score-badge {
      display: inline-block;
      padding: 6px 20px;
      border-radius: 20px;
      font-weight: 700;
      font-size: 15px;
    }
    .score-badge.excelente { background: #dcfce7; color: #166534; }
    .score-badge.bueno     { background: #fef3c7; color: #92400e; }
    .score-badge.desarrollo{ background: #fee2e2; color: #991b1b; }
```

- [ ] **Step 3: Actualizar el JS que muestra el successState**

Localizar estas líneas (alrededor de la 503):

```js
      document.getElementById('loadingState').style.display = 'none';
      document.getElementById('successState').style.display = 'block';
```

Reemplazarlas por:

```js
      document.getElementById('loadingState').style.display = 'none';

      // Inyectar datos del análisis
      document.getElementById('resName').textContent = data.name || '';
      document.getElementById('resFortaleza').textContent = data.fortaleza || '';

      const badge = document.getElementById('resBadge');
      badge.textContent = data.score_label || '';
      const classMap = { 'Excelente': 'excelente', 'Bueno': 'bueno', 'En desarrollo': 'desarrollo' };
      badge.className = 'score-badge ' + (classMap[data.score_label] || '');

      const ul = document.getElementById('resDebilidades');
      ul.innerHTML = '';
      (data.debilidades || []).forEach(d => {
        const li = document.createElement('li');
        li.style.marginBottom = '4px';
        li.textContent = d;
        ul.appendChild(li);
      });

      document.getElementById('successState').style.display = 'block';
```

- [ ] **Step 4: Verificar visualmente**

Correr el servidor:

```bash
cd /Users/lucianocabrera/CVSmart
GEMINI_MOCK=1 uvicorn main:app --reload
```

Abrir `http://localhost:8000/aplicar`, subir cualquier PDF y llenar el formulario. Verificar que:
- Aparece el nombre del candidato en el título
- El badge de color corresponde al nivel (verde/amarillo/rojo)
- Se muestra la fortaleza principal
- Se listan las áreas de oportunidad
- Los botones de navegación funcionan

- [ ] **Step 5: Commit**

```bash
git add frontend/aplicar.html
git commit -m "feat: show analysis results on post-submission screen"
```
