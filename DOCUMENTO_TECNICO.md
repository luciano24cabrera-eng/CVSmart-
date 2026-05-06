# CVSmart V2 - Documento Técnico

## Definición del Problema y Objetivos del Proyecto

**Problema:** Los reclutadores necesitan un sistema eficiente para recibir, analizar, mejorar y gestionar CVs de candidatos, optimizando el proceso de selección de personal.

**Objetivos:**
- Permitir candidatos crear/mejorar CVs con asistencia de IA
- Análisis automático de CVs para extraer datos relevantes
- Panel de control para reclutadores gestionar candidatos
- Comunicación automatizada (emails de retroalimentación y acciones)
- Seguimiento de estados de candidatos (aceptado, agendado, rechazado)

---

## Arquitectura General del Sistema

### Stack Tecnológico

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Backend | FastAPI (Python) | - |
| Frontend | HTML5 + CSS3 + JavaScript Vanilla | - |
| Base de Datos | SQLite | - |
| Servidor Estático | StaticFiles (FastAPI) | - |
| IA/LLMs | Claude API (Anthropic) | - |
| Email | SMTP | - |

### Arquitectura de Capas

```
┌─────────────────────────────────────────────┐
│         Frontend (Presentation)              │
│  ├─ index.html (Landing)                    │
│  ├─ crear-cv.html (CV Creation)             │
│  ├─ aplicar.html (Application Form)         │
│  └─ panel.html (Recruiter Dashboard)        │
├─────────────────────────────────────────────┤
│    FastAPI Backend (Business Logic)         │
│  ├─ API Endpoints (REST)                    │
│  ├─ Auth (Header-based)                     │
│  └─ Request Validation (Pydantic)           │
├─────────────────────────────────────────────┤
│    Service Layer (Core Logic)               │
│  ├─ cv_generator.py (AI-powered CV)         │
│  ├─ analyzer.py (CV Analysis)               │
│  ├─ email_sender.py (Communications)        │
│  └─ database.py (Data Persistence)          │
├─────────────────────────────────────────────┤
│    Data Layer (SQLite Database)             │
│  ├─ candidates                              │
│  ├─ applications                            │
│  └─ audit_logs                              │
└─────────────────────────────────────────────┘
```

---

## Backend - Descripción Técnica

### 1. Componentes Principales

#### **main.py** - Servidor FastAPI
- **Responsabilidad:** Orquestación de endpoints y gestión del ciclo de vida
- **Lifespan:** Inicialización de directorio de CVs y base de datos
- **Rutas principales:**
  - `POST /upload-cv` - Recibir CV de candidato
  - `POST /improve-cv` - Mejorar CV con IA
  - `GET /analyze` - Analizar CV
  - `GET /candidates` - Listar candidatos
  - `GET /candidates/{id}` - Obtener candidato específico
  - `POST /acciones/*` - Aceptar, agendar, rechazar candidatos
  - `GET /generate-pdf` - Generar PDF del CV

#### **database.py** - Gestión de Datos
- **Responsabilidad:** CRUD de candidatos y persistencia
- **Funciones clave:**
  ```python
  - init_db()                    # Crear tablas
  - insert_candidate()           # Registrar nuevo candidato
  - get_all_candidates()        # Listar candidatos
  - update_candidate_estado()   # Cambiar estado (aceptado, agendado, etc.)
  - mark_email_sent()           # Registrar email enviado
  - get_stats()                 # Estadísticas para dashboard
  ```
- **Esquema:**
  ```sql
  candidates (
    id, email, nombre, telefono, ciudad, 
    cv_content, estado, fecha_registro, ...
  )
  ```

#### **cv_generator.py** - Generación de CVs
- **Responsabilidad:** Mejorar CVs usando Claude API
- **Funciones:**
  - `improve_cv_with_ai()` - Refina CV usando prompt de IA
  - `generate_cv_pdf()` - Convierte HTML a PDF
- **Integración:** Claude API para análisis y mejora de contenido

#### **analyzer.py** - Análisis de CVs
- **Responsabilidad:** Extracción de datos estructurados del CV
- **Función principal:**
  - `analyze_cv()` - Retorna JSON con:
    - Información personal
    - Experiencia laboral
    - Educación
    - Habilidades
    - Puntuación general

#### **email_sender.py** - Comunicaciones
- **Responsabilidad:** Envío de emails a candidatos
- **Funciones:**
  - `send_feedback_email()` - Retroalimentación del CV
  - `send_action_email()` - Notificación de acciones (aceptación, rechazo, entrevista)
- **Template:** Emails HTML con estilos profesionales

### 2. Autenticación

**Método:** Header-based con contraseña
```python
require_auth(x_recruiter_password: str = Header(None))
  ├─ Valida contra: SECRET_PANEL (env var)
  └─ Retorna: 401 si credenciales inválidas
```

### 3. Validación de Datos

**Pydantic Models:**
- `AceptarBody` - Validar formato de fecha (YYYY-MM-DD)
- `AgendarBody` - Validar datos de cita
- Validación automática en todos los endpoints

---

## Frontend - Descripción Técnica

### 1. Estructura de Páginas

#### **index.html** - Landing Page
- **Propósito:** Presentación inicial del sistema
- **Componentes:**
  - Descripción de CVSmart
  - Call-to-action para crear CV o aplicar
  - Links a crear-cv.html y aplicar.html

#### **crear-cv.html** - Generador de CVs
- **Propósito:** Permitir candidatos crear/mejorar CVs
- **Features:**
  - Formulario de datos personales
  - Editor de experiencia laboral (dinámico)
  - Editor de educación
  - Editor de habilidades
  - Preview del CV en tiempo real
  - Botón "Mejorar con IA" (llamada a backend)
  - Descarga en PDF

#### **aplicar.html** - Formulario de Aplicación
- **Propósito:** Candidatos envían CVs y formulario
- **Campos:**
  - Email
  - Teléfono
  - Ciudad
  - Upload de CV (file input)
  - Análisis automático del CV
  - Confirmación de aplicación

#### **panel.html** - Dashboard de Reclutadores
- **Propósito:** Gestión de candidatos
- **Secciones:**
  - Tabla de candidatos (filtrable, ordenable)
  - Estados: Pendiente, Aceptado, Agendado, Rechazado
  - Acciones disponibles:
    - Ver detalles
    - Aceptar candidato
    - Agendar entrevista
    - Rechazar candidato
    - Enviar feedback
  - Estadísticas (total candidatos, por estado)
  - Búsqueda y filtros

### 2. Estilos y Diseño

**Ubicación:** `/frontend/styles/`
- **Enfoque:** Dark theme (según notas de diseño)
- **Componentes:**
  - Colores coherentes (primario, secundario, alertas)
  - Tipografía profesional
  - Responsive design (mobile-first)
  - Accesibilidad (WCAG 2.1)

### 3. Lógica de Cliente (JavaScript)

**Patrones:**
- Vanilla JavaScript (sin frameworks)
- Event listeners para interactividad
- Fetch API para llamadas al backend
- LocalStorage para datos temporales
- Validación cliente-side (redundante con backend)

**Flujos principales:**
```
Crear CV:
  candidato llenar datos → preview → mejorar IA → descargar PDF → enviar email

Aplicar:
  upload CV → análisis automático → mostrar datos extraídos → confirmar → crear candidato

Panel:
  reclutador autenticar → ver candidatos → seleccionar acciones → enviar email → registrar estado
```

---

## Flujos de Datos Principales

### Flujo 1: Candidato Crea CV y Aplica

```
1. Candidato accede crear-cv.html
2. Llena formulario de datos personales, experiencia, educación
3. Click "Mejorar con IA"
   → POST /improve-cv {cv_content}
   → Backend: Claude API mejora contenido
   → Retorna CV mejorado
4. Candidato descarga PDF
   → GET /generate-pdf
   → Backend: Convierte HTML → PDF
5. Candidato clic "Aplicar"
   → POST /aplicar {email, telefono, ciudad, cv_file}
   → Backend: insert_candidate() + analyze_cv()
   → Email confirmación a candidato
```

### Flujo 2: Reclutador Gestiona Candidatos

```
1. Reclutador accede panel.html + credenciales (header)
2. Backend valida contraseña (require_auth)
3. GET /candidates (auth required)
   → Retorna lista de candidatos con estados
4. Reclutador selecciona acción: aceptar/agendar/rechazar
   → POST /acciones/{tipo} {candidato_id, datos}
   → Backend: update_candidate_estado() + send_action_email()
   → Email enviado a candidato
5. Dashboard actualiza en tiempo real
```

### Flujo 3: Análisis y Mejora de CV

```
CVS → analyze_cv() → JSON estructurado
     ↓
     → extrae: nombre, email, experiencia, educación, habilidades
     ↓
CV → improve_cv_with_ai() → Claude API
     ↓
     → prompt: "Mejora este CV para posición {role}"
     ↓
     → retorna CV mejorado
```

---

## Calidad y Obtención de Datos

### Validación de Entrada

**Cliente-side:**
- Validación HTML5 (type, required, pattern)
- Validación JavaScript (regex, longitud)

**Servidor-side:**
- Validación Pydantic (automática)
- Sanitización de strings
- Validación de formatos:
  - Email: `\w+@\w+\.\w+`
  - Fecha: `YYYY-MM-DD`
  - Teléfono: formato flexible

### Manejo de Datos Sensibles

- Email y teléfono encriptados en DB (considerar)
- Logs de auditoría para acciones de reclutadores
- Contraseña de panel en env var (no hardcoded)

### Limpieza de Datos

- Trim de whitespace
- Normalización de teléfonos
- Deduplicación por email
- Manejo de valores nulos/duplicados en análisis

---

## Transformaciones y Feature Engineering

### Datos del CV

| Campo Original | Transformación | Campo Resultante |
|---------------|----------------|------------------|
| CV texto bruto | NLP extraction | `nombre`, `email`, `telefono` |
| Historial laboral | Parsing | `exp_años`, `empresas`, `roles` |
| Educación | Classification | `nivel_educativo`, `campos` |
| Texto libre | Embedding | `skills_tags`, `puntuación` |
| CV mejoras IA | Diff comparison | `cambios_realizados` |

### Características Derivadas

```python
edad_aproximada = calcular_desde_educacion_fechas()
años_experiencia = suma(fin_rol - inicio_rol)
seniority = clasificar(años_experiencia)
match_score = similitud_cv_vs_job_description()
```

---

## Modelado - Integraciones Externas

### Claude API (Anthropic)

**Usos:**
1. **Análisis de CV:** Extrae estructura de CV no estructurado
   ```python
   prompt: "Analiza este CV y retorna JSON con nombre, email, experiencia..."
   ```

2. **Mejora de CV:** Refina contenido para posición específica
   ```python
   prompt: f"Mejora este CV para posición {role}. Mantén veracidad, optimiza impacto"
   ```

**Parámetros:**
- Model: claude-3.5-sonnet (o similar)
- Temperature: 0.7 (balance creativo-determinístico)
- Max tokens: 2000

### SMTP (Email)

**Configuración:**
- Host/Port: env vars
- Auth: usuario/contraseña env
- TLS: habilitado

**Templates:**
- Email de bienvenida
- Email de feedback (CV mejoras)
- Email de acción (aceptación/rechazo/entrevista)

---

## Evaluación del Desempeño

### Métricas Clave

| Métrica | Definición | Target |
|---------|-----------|--------|
| **Tasa de CV mejora** | % CVs mejorados exitosamente | > 95% |
| **Tiempo análisis** | Promedio segundos análisis CV | < 5s |
| **Email delivery** | % emails entregados | > 98% |
| **Tasa conversión** | % candidatos que aplican | > 30% |
| **Satisfacción** | Feedback reclutadores | 4.5+/5 |

### Validación de Resultados

**Backend:**
- Unit tests: `tests/test_*.py`
- Integration tests: endpoints + DB
- Load testing: simulación de carga

**Frontend:**
- Browser testing: Chrome, Firefox, Safari
- Responsive: mobile, tablet, desktop
- Accessibility: WCAG 2.1 AA

**Datos:**
- Validation rules en Pydantic
- Logging de errores
- Auditoría de acciones reclutadores

---

## Reproducibilidad y Código

### Estructura de Directorio

```
CVSmart/
├─ main.py                    # Servidor FastAPI
├─ database.py               # CRUD y schemas
├─ cv_generator.py           # Mejora con IA
├─ analyzer.py               # Análisis de CV
├─ email_sender.py           # Envío emails
├─ frontend/
│  ├─ index.html
│  ├─ crear-cv.html
│  ├─ aplicar.html
│  ├─ panel.html
│  └─ styles/
├─ tests/                    # Unit + integration tests
├─ docs/                     # Specs y planes
├─ requirements.txt          # Dependencias Python
├─ .env.example              # Variables de entorno
└─ .gitignore
```

### Configuración de Entorno

**`.env.example`:**
```
FASTAPI_ENV=development
SECRET_PANEL=cvsmart2026

# Claude API
ANTHROPIC_API_KEY=sk-...

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-password

# App config
DB_PATH=./cvsmart.db
```

### Ejecución

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# editar con valores reales

# Ejecutar servidor
python main.py
# Accesible en http://localhost:8000

# Tests
pytest tests/
```

### Estándares de Código

- **Style:** PEP 8 (Python)
- **Type hints:** En funciones críticas
- **Docstrings:** En módulos principales
- **Comments:** Solo lógica compleja o workarounds
- **Naming:** snake_case (Python), camelCase (JS)

### Versionado

- Commits: mensajes descriptivos (fix:, feat:, refactor:)
- Branches: feature/*, bugfix/*, docs/*
- Tags: semantic versioning (v1.0.0)

### Testing

**Cobertura:**
- database.py: 100% (crítico)
- cv_generator.py: 85% (mocks de API)
- analyzer.py: 90%
- email_sender.py: 80% (mocks de SMTP)

**Tipos:**
- Unit: funciones aisladas
- Integration: endpoints + DB
- E2E: flujos completos (manual)

---

## Deployment y Mantenimiento

### Requisitos

- Python 3.9+
- SQLite3
- SMTP acceso
- Claude API key

### Monitoreo

- Logs de errores (archivo)
- Métricas básicas (emails enviados, CVs analizados)
- Alertas para fallos de API o email

### Backups

- Base de datos: diaria
- CVs generados: respaldos incrementales
- Logs: rotación mensual

---

## Conclusiones

CVSmart V2 es un sistema modular que integra IA para optimizar el proceso de selección. La arquitectura separada de capas permite mantenimiento fácil, testing exhaustivo y escalabilidad futura.

**Próximos pasos:**
- Agregar soporte multi-idioma
- Implementar caché de análisis
- Dashboard con analytics avanzados
- Integración con ATS (Applicant Tracking Systems)

