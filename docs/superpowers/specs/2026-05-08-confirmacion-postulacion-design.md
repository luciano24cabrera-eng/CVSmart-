# Diseño: Pantalla de confirmación con resultados del análisis

**Fecha:** 2026-05-08  
**Área:** Experiencia del candidato  
**Enfoque elegido:** Opción A — Enriquecer el estado de éxito inline

---

## Problema

Después de subir un CV, el candidato ve una pantalla genérica que solo dice "revisa tu correo". El análisis de IA ya ocurrió y los datos están disponibles, pero no se muestran al usuario.

## Objetivo

Mostrar al candidato su resultado inmediatamente después de enviar el CV: nivel de perfil, fortaleza principal y áreas de mejora.

---

## Cambios requeridos

### 1. Backend — `main.py`

El endpoint `POST /api/aplicar` actualmente retorna:

```json
{ "success": true, "candidateId": 1, "name": "...", "message": "..." }
```

Agregar al response:
- `score_label` — string: `"Excelente"`, `"Bueno"`, o `"En desarrollo"`
- `score` — número del 1 al 10
- `fortaleza` — string con la fortaleza principal
- `debilidades` — array de strings con áreas de mejora
- `resumen` — string con el resumen ejecutivo

No requiere cambios en la base de datos ni en el analizador.

### 2. Frontend — `frontend/aplicar.html`

**HTML del `successState`:** Reemplazar el contenido estático por una tarjeta dinámica con slots para cada campo:

- Badge de nivel con color dinámico:
  - `Excelente` → verde (`#166534` / `#dcfce7`)
  - `Bueno` → amarillo (`#92400e` / `#fef3c7`)
  - `En desarrollo` → rojo (`#991b1b` / `#fee2e2`)
- Nombre del candidato
- Sección "Tu fortaleza principal" con el texto de `fortaleza`
- Sección "Áreas de oportunidad" con lista de `debilidades`
- Botones: "← Volver al inicio" y "Mejorar mi CV →"

**JavaScript:** Al recibir respuesta exitosa de la API, antes de mostrar `successState`:
1. Leer `score_label`, `fortaleza`, `debilidades`, `name` del response
2. Inyectar valores en los elementos del DOM
3. Aplicar clase de color al badge según `score_label`
4. Mostrar `successState`

---

## Fuera de alcance

- Sin cambios en base de datos
- Sin cambios en emails
- Sin cambios en panel de admin
- Sin nueva página ni redirección

---

## Criterios de éxito

- El candidato ve su nivel de perfil, fortaleza y áreas de mejora inmediatamente al enviar
- El badge cambia de color según el nivel
- Los botones de navegación siguen funcionando
- El flujo de error no se ve afectado
