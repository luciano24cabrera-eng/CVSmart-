# Diseño: Archivo de candidatos con historial

**Fecha:** 2026-05-08  
**Área:** Panel de administrador  
**Enfoque elegido:** Opción B — campo booleano `archivado` separado del estado

---

## Problema

El dashboard del reclutador acumula candidatos que ya no son relevantes (rechazados, descartados). No hay forma de limpiar la vista sin perder los datos.

## Objetivo

Permitir al reclutador archivar candidatos para quitarlos del dashboard principal, preservando su estado original, con posibilidad de restaurarlos desde una sección de historial.

---

## Cambios requeridos

### 1. Base de datos — `database.py`

**Nueva columna:**
```sql
archivado INTEGER DEFAULT 0
```
Agregada a `_NEW_COLS` para migración automática al iniciar la app. Valor `0` = activo, `1` = archivado.

**`get_all_candidates()`:** Agregar `WHERE archivado = 0` para excluir archivados del dashboard.

**Dos funciones nuevas:**
- `archive_candidate(cid: int) -> bool` — ejecuta `UPDATE candidates SET archivado = 1 WHERE id = ?`
- `unarchive_candidate(cid: int) -> bool` — ejecuta `UPDATE candidates SET archivado = 0 WHERE id = ?`
- `get_archived_candidates() -> list` — retorna candidatos con `archivado = 1`, ordenados por `created_at DESC`

### 2. Backend — `main.py`

**Tres endpoints nuevos**, todos protegidos con `Depends(require_auth)`:

```
POST /api/candidatos/{cid}/archivar
POST /api/candidatos/{cid}/desarchivar
GET  /api/panel/historial
```

- `archivar`: llama `archive_candidate(cid)`, retorna `{"success": True}`
- `desarchivar`: llama `unarchive_candidate(cid)`, retorna `{"success": True}`
- `historial`: llama `get_archived_candidates()`, retorna `{"candidates": [...]}`

Ambas acciones retornan 404 si el candidato no existe.

### 3. Frontend — `panel.html`

**Botón "Archivar" en la tabla principal:**
- Ícono de archivo (`⊗` o similar) en cada fila, al lado de las acciones existentes
- Al hacer click, llama `POST /api/candidatos/{cid}/archivar` con header de auth
- Si respuesta 200: elimina la fila de la tabla con animación fade-out
- Si error: muestra toast de error

**Sección "Historial" debajo de la tabla principal:**
- Encabezado colapsable "Historial de candidatos archivados" con contador
- Tabla con columnas: Nombre, Email, Score, Estado original, Fecha
- Botón "Restaurar" por fila: llama `POST /api/candidatos/{cid}/desarchivar`
- Al restaurar: elimina la fila del historial con fade-out y llama `loadDashboard()` para refrescar la tabla principal automáticamente
- La sección se carga al abrir el panel junto con el dashboard principal

---

## Fuera de alcance

- Sin eliminación permanente de candidatos
- Sin filtros adicionales en el historial
- Sin paginación (suficiente para el scope actual)

---

## Criterios de éxito

- Candidatos archivados desaparecen del dashboard sin recargar la página
- Su estado original (pendiente, rechazado, etc.) se preserva en el historial
- Restaurar un candidato lo regresa al dashboard con su estado original
- La migración de BD es automática y no rompe datos existentes
