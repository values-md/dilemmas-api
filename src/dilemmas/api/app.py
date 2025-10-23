"""FastAPI application for exploring dilemmas."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB
from dilemmas.models.dilemma import Dilemma
from dilemmas.models.judgement import Judgement

app = FastAPI(title="VALUES.md Dilemma Explorer")

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """List all dilemmas."""
    db = get_database()

    async for session in db.get_session():
        statement = select(DilemmaDB).order_by(DilemmaDB.created_at.desc())
        result = await session.execute(statement)
        dilemmas_db = result.scalars().all()

        # Convert to domain models
        dilemmas = [db_dilemma.to_domain() for db_dilemma in dilemmas_db]

    await db.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "dilemmas": dilemmas,
            "count": len(dilemmas),
        },
    )


@app.get("/dilemma/{dilemma_id}", response_class=HTMLResponse)
async def view_dilemma(request: Request, dilemma_id: str):
    """View a single dilemma."""
    db = get_database()

    async for session in db.get_session():
        db_dilemma = await session.get(DilemmaDB, dilemma_id)

        if not db_dilemma:
            raise HTTPException(status_code=404, detail="Dilemma not found")

        dilemma = db_dilemma.to_domain()

    await db.close()

    # Render the situation with default values
    rendered_situation = dilemma.render()

    return templates.TemplateResponse(
        "dilemma.html",
        {
            "request": request,
            "dilemma": dilemma,
            "rendered_situation": rendered_situation,
        },
    )


@app.get("/api/dilemmas", response_model=list[Dilemma])
async def list_dilemmas_api():
    """API endpoint to get all dilemmas as JSON."""
    db = get_database()

    async for session in db.get_session():
        statement = select(DilemmaDB).order_by(DilemmaDB.created_at.desc())
        result = await session.execute(statement)
        dilemmas_db = result.scalars().all()
        dilemmas = [db_dilemma.to_domain() for db_dilemma in dilemmas_db]

    await db.close()
    return dilemmas


@app.get("/api/dilemma/{dilemma_id}", response_model=Dilemma)
async def get_dilemma_api(dilemma_id: str):
    """API endpoint to get a single dilemma as JSON."""
    db = get_database()

    async for session in db.get_session():
        db_dilemma = await session.get(DilemmaDB, dilemma_id)

        if not db_dilemma:
            raise HTTPException(status_code=404, detail="Dilemma not found")

        dilemma = db_dilemma.to_domain()

    await db.close()
    return dilemma


@app.get("/judgements", response_class=HTMLResponse)
async def list_judgements(request: Request):
    """List all judgements."""
    db = get_database()

    async for session in db.get_session():
        # Get all judgements
        statement = select(JudgementDB).order_by(JudgementDB.created_at.desc())
        result = await session.execute(statement)
        judgements_db = result.scalars().all()

        # Convert to domain models
        judgements = [jdb.to_domain() for jdb in judgements_db]

        # Also load dilemmas to show titles
        dilemma_ids = [j.dilemma_id for j in judgements]
        dilemma_statement = select(DilemmaDB).where(DilemmaDB.id.in_(dilemma_ids))
        dilemma_result = await session.execute(dilemma_statement)
        dilemmas_db = {d.id: d.to_domain() for d in dilemma_result.scalars().all()}

    await db.close()

    return templates.TemplateResponse(
        "judgements.html",
        {
            "request": request,
            "judgements": judgements,
            "dilemmas": dilemmas_db,
            "count": len(judgements),
        },
    )


@app.get("/judgement/{judgement_id}", response_class=HTMLResponse)
async def view_judgement(request: Request, judgement_id: str):
    """View a single judgement with its dilemma."""
    db = get_database()

    async for session in db.get_session():
        db_judgement = await session.get(JudgementDB, judgement_id)

        if not db_judgement:
            raise HTTPException(status_code=404, detail="Judgement not found")

        judgement = db_judgement.to_domain()

        # Also load the dilemma
        db_dilemma = await session.get(DilemmaDB, judgement.dilemma_id)
        dilemma = db_dilemma.to_domain() if db_dilemma else None

    await db.close()

    return templates.TemplateResponse(
        "judgement.html",
        {
            "request": request,
            "judgement": judgement,
            "dilemma": dilemma,
        },
    )
