# Acciones del panel de reclutador: Aprobar, Agendar, Descartar

**Fecha:** 2026-05-01
**Estado:** Diseño aprobado
**Archivos afectados:** `database.py`, `main.py`, `email_sender.py`, `frontend/panel.html`

## Problema

El panel del reclutador (`frontend/panel.html`) tiene tres botones en el modal de detalle del candidato — **Aprobar**, **Agendar**, **Descartar** — pero no tienen `onclick` handler ni endpoint de backend. No hacen nada.

Necesitamos:
1. Que cada botón cambie el estado del candidato y lo persista.
2. Que envíe un email automático al candidato con el resultado.
3. Que "Agendar" pida fecha/hora y opcional lugar.
4. Que el panel muestre el estado en la tabla y en el modal.

## Decisiones tomadas durante brainstorming

- **Comportamiento:** cambio de estado **+ email automático**. (Opción B)
- **UX de agendado:** mini-modal dentro del modal con `datetime-local` y campo opcional de lugar/link. (Opción B)
- **Feedback al reclutador:** cierra modal → toast de éxito → badge de estado en la fila. (Opción A)
- **Modelo de datos:** una columna `status` + columnas auxiliares en `candidates`. Sin tabla histórica. (Opción A — YAGNI)

## Diseño

### 1. Base de datos

Tres nuevas columnas en `candidates`:

| Columna | Tipo | Default | Notas |
|---|---|---|---|
| `status` | TEXT | `'pending'` | Valores: `pending`, `approved`, `scheduled`, `rejected` |
| `interview_at` | TEXT (ISO 8601) | NULL | Solo se llena cuando `status='scheduled'` |
| `interview_location` | TEXT | NULL | Lugar o link (Meet/Zoom/oficina). Opcional. |

**Migración:** `init_db()` en `database.py` chequea con `PRAGMA table_info(candidates)` qué columnas faltan y las añade con `ALTER TABLE ADD COLUMN`. SQLite no soporta `IF NOT EXISTS` en ALTER, por eso el chequeo manual. La DB existente (`cvsmart.db`) se migra automáticamente al iniciar el server, sin pérdida de datos.

**Funciones nuevas** en `database.py`:

```python
def update_candidate_status(
    candidate_id: int,
    status: str,
    interview_at: str | None = None,
    interview_location: str | None = None,
) -> bool:
    """Actualiza el estado del candidato. Devuelve True si se actualizó una fila."""
```

`get_all_candidates()` y `get_candidate()` deben incluir las tres nuevas columnas en el SELECT y en el dict devuelto.

### 2. Backend (endpoint + email)

**Endpoint nuevo** en `main.py`:

```
POST /api/panel/candidatos/{cid}/accion
Headers: X-Recruiter-Password: <secret>
Body: {
  "action": "approve" | "schedule" | "reject",
  "interview_at": "2026-05-15T10:00",       // requerido si action=schedule
  "interview_location": "Google Meet"       // opcional
}
Response: { "success": true, "status": "approved", "email_sent": true }
```

**Lógica:**

1. `Depends(require_auth)` reutiliza la auth existente.
2. Validar que `cid` existe (`get_candidate`); si no, 404.
3. Si `action == "schedule"`:
   - `interview_at` requerido (400 si falta)
   - Parsear como ISO 8601; rechazar si no parsea (400)
   - Rechazar si la fecha es pasada (400) — comparación contra `datetime.now()`
4. Mapeo `action → status`:
   - `approve` → `approved`
   - `schedule` → `scheduled`
   - `reject` → `rejected`
   - cualquier otro valor → 400
5. Llamar `update_candidate_status(cid, status, interview_at, interview_location)`.
6. Si `candidate.email`: llamar `send_action_email(...)`. Si falla, log y continuar — `email_sent=False`. **No falla la acción si falla el email** (mismo patrón que `/api/aplicar`).
7. Devolver `{ success, status, email_sent }`.

**Email** — Función nueva en `email_sender.py`:

```python
def send_action_email(
    to_email: str,
    name: str,
    action: str,                          # "approve" | "schedule" | "reject"
    interview_at: str | None = None,      # solo para schedule
    interview_location: str | None = None,
) -> bool:
    """Envía el email correspondiente según la acción. Devuelve True si se envió."""
```

**Templates** (en español, tono CVSmart):

| Acción | Asunto | Cuerpo (resumen) |
|---|---|---|
| approve | "Avanzas en el proceso — CVSmart" | "Hola {nombre}, ¡buenas noticias! Tu perfil avanza a la siguiente etapa..." |
| schedule | "Tu entrevista en CVSmart" | "Hola {nombre}, te confirmamos tu entrevista para el {fecha formateada}{ en {lugar} si existe}..." |
| reject | "Resultado de tu postulación — CVSmart" | "Hola {nombre}, gracias por aplicar. En esta ocasión no avanzaremos contigo..." |

La fecha se formatea en español (ej. "15 de mayo de 2026, 10:00 hrs") usando el locale del sistema o un mapeo manual de meses si el locale no está disponible (más portable).

### 3. Frontend: modal de agendar + acciones

#### 3.1 Mini-modal de agendar

Cuando el reclutador hace clic en "Agendar", el contenido del modal de detalle se reemplaza por una vista de agendado (mismo modal-overlay, mismo `.modal`, distinto contenido):

```
┌─ [icono] Agendar entrevista ─┐
│         {nombre candidato}    │
│                                │
│  Fecha y hora *               │
│  [datetime-local input]       │
│                                │
│  Lugar / link (opcional)      │
│  [text input]  Google Meet…   │
│                                │
│  [Cancelar]  [Confirmar y →]  │
└────────────────────────────────┘
```

Implementación: una función `showScheduleForm(candidateId, candidateName)` que oculta `.modal-inner` y muestra un `<div id="scheduleForm">` con el formulario. "Cancelar" vuelve al modal de detalle; "Confirmar" llama `doAction('schedule', { interview_at, interview_location })`.

**Estilos:** reutiliza `.modal-section`, `.action-btn`, `.btn-download`. El `<input type="datetime-local">` usa el mismo styling oscuro que los demás inputs (background `#111`, border `rgba(255,255,255,0.08)`, focus rojo).

**Validación cliente:** `min={today's ISO string}` en el input para prevenir fechas pasadas. Botón "Confirmar" deshabilitado mientras `interview_at` está vacío.

#### 3.2 Botones del modal de detalle

Wire-up en `panel.html`. Los tres botones existentes (`.action-approve`, `.action-schedule`, `.action-discard`) reciben handlers en `openModal()`:

```js
document.querySelector('.action-approve').onclick = () => doAction('approve');
document.querySelector('.action-schedule').onclick = () => showScheduleForm(id, c.name);
document.querySelector('.action-discard').onclick = () => {
  if (confirm('¿Descartar a este candidato? Se le enviará un email.')) doAction('reject');
};
```

`doAction(action, extras = {})` hace POST a `/api/panel/candidatos/${currentId}/accion`, actualiza `_cachedCandidates` localmente con los campos devueltos por el backend, cierra el modal, dispara toast, re-renderiza ambas tablas.

#### 3.3 Toast de éxito

Componente nuevo (HTML + CSS + JS) para notificación abajo-derecha, autocerrar a 4s con animación de slide-in/slide-out:

```js
showToast(message, variant)
// variant: 'success-green' | 'success-yellow' | 'success-red'
```

Mensajes:
- approve: "Candidato aprobado · Email enviado"
- schedule: "Entrevista agendada · Email enviado"
- reject: "Candidato descartado · Email enviado"

Si `email_sent=false`, el sufijo cambia a "· Email no enviado" y el toast es naranja.

### 4. Frontend: badges en la tabla

#### 4.1 Badge de estado por fila

El badge se inserta dentro de la celda `.col-name` (no una columna nueva del `<table>` para no romper el grid responsive):

```html
<td class="col-name">
  Juan Pérez
  <span class="status-badge status-approved">✓ Aprobado</span>
</td>
```

**Reglas de renderizado:**
- `status === 'pending'` → sin badge (estado por defecto, sin ruido visual)
- `status === 'approved'` → badge verde `#22c55e`, texto "✓ Aprobado"
- `status === 'scheduled'` → badge amarillo `#eab308`, texto "◷ Agendado", `title` con fecha formateada al hover
- `status === 'rejected'` → badge gris translúcido, texto "✕ Descartado", **toda la fila** con `opacity: 0.5` para que se vea "apagada" pero siga visible

**Estilos:** misma forma que `.skill-tag` (pill pequeño, padding 4px 10px, font-size 0.7rem, border-radius 100px), con colores por estado.

Aplica a ambas tablas: `#candidatesGrid` (Dashboard) y `#candidatesGrid2` (Candidatos).

#### 4.2 Re-render tras acción

`doAction()` actualiza el candidato en `_cachedCandidates` con los nuevos campos (`status`, `interview_at`, `interview_location`) que vienen en la respuesta del backend, luego llama a las funciones de render existentes para repintar ambas tablas. **No se hace fetch adicional** — los datos del backend en la respuesta son la fuente de verdad.

#### 4.3 Modal recordando estado

Al reabrir el modal de un candidato ya procesado, se inserta una línea informativa debajo de `mEmail` (en `.modal-title` o como `.modal-section` nueva al inicio):

```
Estado: Agendado · 15 de mayo de 2026, 10:00 · Google Meet
```

Esta línea solo aparece si `status !== 'pending'`. Para `approved`/`rejected` se omite el sufijo de fecha/lugar.

**Los tres botones de acción siguen visibles** — el reclutador puede cambiar de opinión (aprobar a un descartado, re-agendar, etc.). Cualquier nueva acción sobreescribe el estado anterior. No se mantiene histórico (decisión deliberada — ver "Decisiones tomadas" arriba).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Fecha de entrevista pasada/inválida | 400 del backend → toast rojo "Fecha inválida" |
| Candidato no existe | 404 → toast rojo "Candidato no encontrado" |
| Auth incorrecta (token expirado) | 401 → forzar logout |
| Email falla | Acción se completa igual; toast naranja "Email no enviado" |
| Network error | Toast rojo "Error de conexión, intenta de nuevo"; estado no cambia |

## Testing

Tests nuevos en `tests/test_database.py`:
- `update_candidate_status` con cada acción
- Migración: simular DB sin las nuevas columnas, llamar `init_db()`, verificar que las columnas existen

Test manual del frontend (no hay test runner para frontend en este proyecto):
- Aprobar candidato → verifica badge verde + email recibido
- Agendar candidato → mini-modal aparece, validación de fecha, badge amarillo, tooltip con fecha
- Descartar candidato → confirm dialog, fila opaca, badge gris
- Re-abrir modal de candidato procesado → muestra línea de estado
- Cambiar de opinión (descartar → aprobar) → estado se sobreescribe correctamente

## Out of scope (YAGNI)

- Histórico de cambios de estado (ningún flujo del producto lo necesita hoy)
- Filtro "Mostrar solo descartados" / "Ocultar descartados" (los descartados ya tienen visual diferenciado)
- Recordatorio automático antes de la entrevista (cron job, fuera del alcance)
- Editar fecha de una entrevista ya agendada como flujo separado (se hace re-agendando, que es válido)
- Plantillas de email personalizables por el reclutador (templates fijos por ahora)
