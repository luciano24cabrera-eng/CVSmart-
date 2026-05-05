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
    # load_dotenv() must run before env vars are read — already done at module top
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
