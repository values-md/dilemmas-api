"""FastAPI application for exploring dilemmas."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB
from dilemmas.models.dilemma import Dilemma

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
