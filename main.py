import os, json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Body, Header
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv

load_dotenv()

from database import init_db, insert_candidate, get_all_candidates, get_stats, get_candidate, mark_email_sent
from analyzer import analyze_cv
from email_sender import send_feedback_email
from cv_generator import improve_cv_with_ai, generate_cv_pdf

CVS_DIR = Path("cvs")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # load_dotenv() must run before env vars are read — already done at module top
    CVS_DIR.mkdir(exist_ok=True)
    init_db()
    yield

app = FastAPI(title="CVSmart V2", lifespan=lifespan)

# ── Auth ──────────────────────────────────────────────────────────────
def require_auth(x_recruiter_password: str = Header(None)):
    if x_recruiter_password != os.getenv("SECRET_PANEL", "cvsmart2026"):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

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
def serve_aplicar(): return FileResponse("frontend/aplicar.html")

@app.get("/panel", include_in_schema=False)
def serve_panel(): return FileResponse("frontend/panel.html")

@app.get("/crear-cv", include_in_schema=False)
def serve_crear_cv(): return FileResponse("frontend/crear-cv.html")
