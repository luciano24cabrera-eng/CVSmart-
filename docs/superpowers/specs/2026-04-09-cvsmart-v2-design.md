# CVSmart V2 — Design Spec
**Date:** 2026-04-09  
**Stack:** Python 3.11 + FastAPI + SQLite + Groq (llama-3.3-70b-versatile) + reportlab + smtplib  
**Replaces:** Node.js/Express V1 in `/Users/lucianocabrera/CVSmart/`

---

## 1. Overview

CVSmart V2 is an AI-powered CV filtering system for recruiters. Candidates submit their CV via a web form; Groq analyzes the profile and scores it 1–10; the recruiter sees a prioritized dashboard. New in V2: automatic feedback email to candidates, and a CV creator where users fill a form and AI generates a polished downloadable PDF.

---

## 2. Architecture

Single Python/FastAPI process on port 8000 serving both the API and static frontend files.

```
CVSmart/
├── main.py              # FastAPI app, all routes, static file serving
├── database.py          # SQLite init and query helpers
├── analyzer.py          # Groq CV analysis (text extraction + scoring)
├── email_sender.py      # Gmail SMTP, HTML email template
├── cv_generator.py      # Groq CV improvement + reportlab PDF generation
├── requirements.txt
├── .env
├── .env.example
├── cvs/                 # Uploaded candidate CVs (PDF)
└── frontend/
    ├── index.html       # Landing page
    ├── aplicar.html     # Candidate application form
    ├── panel.html       # Recruiter dashboard (password protected)
    └── crear-cv.html    # AI CV creator
```

---

## 3. Database

Single SQLite file: `cvsmart.db`

```sql
CREATE TABLE candidates (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  name                TEXT NOT NULL,
  email               TEXT,
  phone               TEXT,
  cv_filename         TEXT NOT NULL,
  cv_original_name    TEXT,
  score               REAL DEFAULT 0,
  score_label         TEXT,        -- "Excelente" | "Bueno" | "En desarrollo"
  years_experience    REAL,
  education_level     TEXT,
  matching_skills     TEXT DEFAULT '[]',  -- JSON array
  summary             TEXT,
  strength            TEXT,        -- top strength detected by AI
  weaknesses          TEXT,        -- JSON array of 2 improvement areas
  full_analysis       TEXT DEFAULT '{}',  -- full Groq JSON response
  availability        TEXT,
  expected_salary     TEXT,
  specific_experience TEXT,
  email_sent          INTEGER DEFAULT 0,  -- 1 once email delivered
  created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

---

## 4. API Routes

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| `POST` | `/api/aplicar` | None | Upload CV + form, analyze, save, send email |
| `GET`  | `/api/panel/candidatos` | Password header | List all candidates ordered by score desc |
| `GET`  | `/api/panel/stats` | Password header | Total, avg score, high/mid/low counts |
| `GET`  | `/api/panel/candidatos/{id}` | Password header | Full candidate detail |
| `GET`  | `/api/panel/candidatos/{id}/cv` | Password header | Download original PDF |
| `POST` | `/api/generar-cv` | None | Receive form data, return generated CV as PDF |

Password auth: header `X-Recruiter-Password` checked against `SECRET_PANEL` env var (`cvsmart2026`).

---

## 5. CV Analysis Flow (`analyzer.py`)

1. Receive uploaded PDF bytes
2. Extract text with `pdfplumber`
3. Send to Groq with structured prompt requesting JSON:
```json
{
  "nombre": "",
  "años_experiencia": 0,
  "nivel_estudios": "",
  "habilidades_coincidentes": [],
  "puntaje": 7,
  "resumen": "",
  "fortaleza": "",
  "debilidades": ["area1", "area2"]
}
```
4. Parse JSON, derive `score_label`:
   - 8–10 → "Excelente"
   - 5–7  → "Bueno"
   - 1–4  → "En desarrollo"
5. Return structured dict to `main.py`

---

## 6. Email Flow (`email_sender.py`)

Triggered immediately after analysis completes, before returning response to frontend.

- **Transport:** `smtplib.SMTP_SSL("smtp.gmail.com", 465)`
- **Credentials:** `GMAIL_USER` + `GMAIL_APP_PASSWORD` from `.env`
- **Subject:** `CVSmart — Recibimos tu CV, aquí está tu retroalimentación`
- **Body:** HTML email with:
  - Greeting with candidate name
  - Confirmation of receipt
  - Score level badge (color-coded: green/yellow/red)
  - Top strength detected
  - 2 improvement areas as bullets
  - CTA to CVSmart CV Creator
  - Footer: Equipo CVSmart
- On success: set `email_sent = 1` in DB
- On failure: log error, do NOT fail the main request — candidate submission still succeeds

---

## 7. CV Generator Flow (`cv_generator.py`)

1. Frontend POSTs JSON with: nombre, contacto, puesto_objetivo, resumen, experiencia (up to 3), educacion (up to 2), habilidades_tecnicas, habilidades_blandas, idiomas
2. Groq called with HR expert prompt → returns polished JSON with same structure
3. `reportlab` builds PDF in `BytesIO`:
   - Navy blue header bar with name + contact
   - Sections: Resumen Profesional, Experiencia, Educación, Habilidades Técnicas, Habilidades Blandas, Idiomas
   - Clean typography (Helvetica), professional margins
4. FastAPI returns `StreamingResponse(pdf_bytes, media_type="application/pdf")` with `Content-Disposition: attachment; filename="CV-{nombre}.pdf"`
5. PDF is NOT saved to disk — generated in memory per request

---

## 8. Frontend Pages

All pages share: Inter font (Google Fonts), color palette `#1F3864` / `#2E75B6` / `#4FC3F7` / `#F8FAFF`, glassmorphism cards, gradient buttons, fixed navbar, fully responsive.

### `index.html` — Landing
- Hero: title, subtitle, CTA button ("Subir mi CV")
- "¿Cómo funciona?" — 3 visual steps with icons
- Benefits section with feature cards
- Footer
- No mention of WhatsApp — only web form as intake channel

### `aplicar.html` — Candidate Form
- Centered card layout
- Fields: email (required), phone (optional)
- Drag & drop PDF upload zone with animated progress bar
- 3 filter questions: availability (select), expected salary (text), years of experience (number)
- Animated loading state during analysis
- Success screen: confirmation + notice that feedback email is on its way (no score shown)

### `panel.html` — Recruiter Dashboard
- Login screen with password `cvsmart2026`
- Dashboard counters: total candidates, avg score, top candidates (8+)
- Table with: avatar (initials), name, score badge (green/yellow/red), date, "Ver detalle" button
- Modal with: summary, skills, filter answers, strength, weaknesses, download CV button

### `crear-cv.html` — AI CV Creator
- Multi-section form: personal info, professional summary, up to 3 work experiences, up to 2 education entries, technical skills (dynamic tags), soft skills (dynamic tags), languages
- "Generar CV con IA" button → POST to `/api/generar-cv`
- Preview panel shows generated CV data
- Download PDF button

---

## 9. Environment Variables (`.env.example`)

```
GROQ_API_KEY=tu_clave_aqui
SECRET_PANEL=cvsmart2026
GMAIL_USER=tu_correo@gmail.com
GMAIL_APP_PASSWORD=tu_app_password_aqui
```

---

## 10. Dependencies (`requirements.txt`)

```
fastapi
uvicorn[standard]
python-multipart
pdfplumber
groq
reportlab
python-dotenv
```

---

## 11. Run Instructions

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# Opens at http://localhost:8000
```
