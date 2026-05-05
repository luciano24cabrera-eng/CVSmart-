# Diseño: Panel Acciones — Aceptar / Agendar / Rechazar

**Fecha:** 2026-05-05  
**Proyecto:** CVSmart  
**Alcance:** Conectar los botones de acción del modal de detalle del panel reclutador con lógica de negocio completa (BD + email).

---

## Contexto

El `panel.html` ya tiene un modal de detalle de candidato con tres botones: `.action-approve` (Aprobar), `.action-schedule` (Agendar), `.action-discard` (Descartar). Actualmente no hacen nada. Este spec define la implementación completa.

**Flujo elegido:** Los botones viven dentro del modal de detalle. El admin abre el perfil del candidato y desde ahí ejecuta la acción. No se agregan botones directamente en la tabla.

---

## Arquitectura

```
Modal de detalle → clic en acción
    → openSubModal(action, candidateId)
    → sub-modal de confirmación (inline HTML)
    → fetch POST /api/candidatos/{id}/{accion}  [con X-Recruiter-Password]
    → endpoint FastAPI → UPDATE BD → send_action_email()
    → JSON { success, email_sent, warning? }
    → toast + badge de estado + botones deshabilitados
```

---

## Base de datos (`database.py`)

### Columnas nuevas en `candidates`

| Columna | Tipo | Default | Uso |
|---------|------|---------|-----|
| `estado` | TEXT | `'pendiente'` | pendiente \| aceptado \| agendado \| rechazado |
| `fecha_inicio` | TEXT | NULL | Fecha de inicio (acción Aceptar) |
| `fecha_cita` | TEXT | NULL | Fecha de la cita (acción Agendar) |
| `hora_cita` | TEXT | NULL | Hora de la cita (acción Agendar) |
| `notas_cita` | TEXT | NULL | Notas adicionales (acción Agendar, opcional) |

### Migración

`init_db()` agrega las columnas con `ALTER TABLE ... ADD COLUMN` envuelto en `try/except` para tolerancia a reinicios (SQLite no soporta `IF NOT EXISTS` en ALTER TABLE).

### Nueva función

```python
def update_candidate_estado(candidate_id, estado, **extra_fields) -> bool
```

Actualiza `estado` más cualquier campo adicional (fecha_inicio, fecha_cita, etc.).

---

## Backend (`main.py`)

### Endpoints nuevos

```
POST /api/candidatos/{id}/aceptar
  Header: X-Recruiter-Password
  Body:   { "fecha_inicio": "YYYY-MM-DD" }
  → estado = "aceptado", guarda fecha_inicio
  → envía email de bienvenida
  → { success, email_sent, warning? }

POST /api/candidatos/{id}/agendar
  Header: X-Recruiter-Password
  Body:   { "fecha_cita": "YYYY-MM-DD", "hora_cita": "HH:MM", "notas": "" }
  → estado = "agendado", guarda fecha_cita + hora_cita + notas_cita
  → envía email de cita agendada
  → { success, email_sent, warning? }

POST /api/candidatos/{id}/rechazar
  Header: X-Recruiter-Password
  Body:   {}
  → estado = "rechazado"
  → envía email de rechazo empático
  → { success, email_sent, warning? }
```

**Manejo de errores:** Si el email falla, el endpoint igual devuelve HTTP 200 con `email_sent: false` y `warning: "<mensaje>"`. El estado en BD siempre se actualiza.

---

## Email (`email_sender.py`)

### Nueva función

```python
def send_action_email(to_email, name, action, **kwargs) -> bool
```

`action` es uno de `"aceptado"`, `"agendado"`, `"rechazado"`.

Lee `NOMBRE_EMPRESA` del `.env` (default `"CVSmart"`).

### Plantillas (HTML, mismo estilo visual que `send_feedback_email`)

#### Aceptar
- **Asunto:** `¡Felicidades! Has sido aceptado en {empresa}`
- **Cuerpo:** Saludo, fecha de inicio destacada, mensaje de bienvenida, firma.

#### Agendar
- **Asunto:** `Tienes una cita agendada con {empresa}`
- **Cuerpo:** Saludo, fecha + hora + notas (la línea de notas se omite si está vacía), instrucción de confirmar asistencia, firma.

#### Rechazar
- **Asunto:** `Actualización sobre tu proceso de selección en {empresa}`
- **Cuerpo:** Agradecimiento, mensaje empático de rechazo, ánimo para futuras postulaciones, firma.

---

## Frontend (`panel.html`)

### Sub-modales (3 nuevos, inline)

**`#modalAceptar`**
- Campo: Nombre del candidato (read-only, cargado automáticamente)
- Campo: Fecha de inicio (date picker, requerido)
- Botón: "Confirmar aceptación"

**`#modalAgendar`**
- Campo: Nombre del candidato (read-only)
- Campo: Fecha de la cita (date picker, requerido)
- Campo: Hora de la cita (time picker, requerido)
- Campo: Notas adicionales (textarea, opcional)
- Botón: "Confirmar cita"

**`#modalRechazar`**
- Campo: Nombre del candidato (read-only)
- Texto: "¿Estás seguro? Se enviará un correo de notificación."
- Botón: "Confirmar rechazo"

Todos cierran al hacer clic fuera o presionar Escape. Se apilan sobre el modal de detalle (z-index superior).

### Wiring de botones existentes

Los botones `.action-approve`, `.action-schedule`, `.action-discard` del modal de detalle llaman a `openSubModal(action, candidateId, candidateName)`.

### Post-acción

1. Sub-modal se cierra.
2. Modal de detalle: los 3 botones de acción se deshabilitan y cambian de apariencia (opacity reducida).
3. Badge de estado aparece/actualiza en el header del modal con color semántico:
   - Aceptado → verde (`#22c55e`)
   - Agendado → azul (`#3b82f6`)
   - Rechazado → rojo apagado con texto tachado implícito (`#a0a0a0`)
4. Toast en esquina inferior derecha (~3 segundos):
   - Éxito: "✓ Candidato aceptado. Correo enviado."
   - Warning: "✓ Estado actualizado. No se pudo enviar el correo."
5. `_cachedCandidates` se actualiza en memoria: el candidato afectado recibe el nuevo `estado`.
6. La tabla de candidatos muestra una nueva columna **Estado** (entre Score y Acciones) con badge de color. Se renderea desde `_cachedCandidates`, por lo que la fila de la tabla se actualiza inmediatamente sin recargar.

### Columna Estado en tabla

Se agrega columna `Estado` a ambas tablas (`candidatesGrid` y `candidatesGrid2`). Badge pequeño inline:
- `pendiente` → gris
- `aceptado` → verde
- `agendado` → azul
- `rechazado` → rojo apagado

---

## Variable de entorno nueva

```env
NOMBRE_EMPRESA=CVSmart
```

Agregar a `.env.example` y documentar en README si existe.

---

## Archivos modificados

| Archivo | Tipo de cambio |
|---------|----------------|
| `database.py` | Agregar columnas + `update_candidate_estado()` |
| `email_sender.py` | Agregar `send_action_email()` + 3 builders HTML |
| `main.py` | Agregar 3 endpoints POST |
| `frontend/panel.html` | 3 sub-modales + wiring JS + toast + badge |
| `.env.example` | Agregar `NOMBRE_EMPRESA` |

---

## Prueba rápida con curl

```bash
# Aceptar candidato ID 1
curl -X POST http://localhost:8000/api/candidatos/1/aceptar \
  -H "X-Recruiter-Password: cvsmart2026" \
  -H "Content-Type: application/json" \
  -d '{"fecha_inicio": "2026-06-01"}'

# Agendar candidato ID 1
curl -X POST http://localhost:8000/api/candidatos/1/agendar \
  -H "X-Recruiter-Password: cvsmart2026" \
  -H "Content-Type: application/json" \
  -d '{"fecha_cita": "2026-05-15", "hora_cita": "10:00", "notas": "Entrevista por Zoom"}'

# Rechazar candidato ID 1
curl -X POST http://localhost:8000/api/candidatos/1/rechazar \
  -H "X-Recruiter-Password: cvsmart2026" \
  -H "Content-Type: application/json" \
  -d '{}'
```
