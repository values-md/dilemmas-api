"""FastAPI application for exploring dilemmas."""

import io
import os
import zipfile
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlmodel import or_, select

from dilemmas.api.auth import verify_api_key
from dilemmas.api.research_parser import parse_research_folder, parse_yaml_frontmatter, render_markdown
from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB
from dilemmas.models.dilemma import Dilemma
from dilemmas.models.judgement import Judgement
from dilemmas.services.generator import DilemmaGenerator

app = FastAPI(
    title="VALUES.md Dilemmas API",
    description="Research project on LLM ethical decision-making",
    version="1.0.0",
)

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Research folder for parsing experiments
RESEARCH_DIR = Path(__file__).parent.parent.parent.parent / "research"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class GenerateRequest(BaseModel):
    """Request model for generating a dilemma."""

    difficulty: int = Field(..., ge=1, le=10, description="Target difficulty (1-10)")
    prompt_version: str | None = Field(None, description="Prompt version (e.g., 'v8_concise')")
    add_variables: bool | None = Field(None, description="Extract variables for bias testing")
    num_actors: int | None = Field(None, ge=1, le=5, description="Number of actors to include")
    num_stakes: int | None = Field(None, ge=1, le=5, description="Number of stakes to include")


class DilemmaListResponse(BaseModel):
    """Response model for paginated dilemma list."""

    items: list[Dilemma]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    """Response model for database statistics."""

    dilemmas_count: int
    judgements_count: int
    experiments_count: int
    models_tested: list[str]
    difficulty_distribution: dict[int, int]


# ============================================================================
# PUBLIC ROUTES - Dilemma Browser
# ============================================================================


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


# ============================================================================
# PUBLIC ROUTES - Research Findings
# ============================================================================


@app.get("/research", response_class=HTMLResponse)
async def research_index(request: Request):
    """List all research experiments."""
    if not RESEARCH_DIR.exists():
        return templates.TemplateResponse(
            "research_index.html",
            {"request": request, "experiments": [], "error": "Research folder not found"},
        )

    experiments = parse_research_folder(RESEARCH_DIR)

    return templates.TemplateResponse(
        "research_index.html",
        {"request": request, "experiments": experiments},
    )


@app.get("/research/guide", response_class=HTMLResponse)
async def research_guide(request: Request):
    """Reproducibility guide for research experiments."""
    guide_path = RESEARCH_DIR / "GUIDE.md"

    if not guide_path.exists():
        raise HTTPException(status_code=404, detail="Guide not found")

    guide_markdown = guide_path.read_text()

    # Strip YAML frontmatter if present (though GUIDE.md shouldn't have it)
    frontmatter, markdown_content = parse_yaml_frontmatter(guide_markdown)
    guide_html = render_markdown(markdown_content)

    return templates.TemplateResponse(
        "research_guide.html",
        {
            "request": request,
            "guide_html": guide_html,
        },
    )


@app.get("/research/{experiment_slug}", response_class=HTMLResponse)
async def research_detail(request: Request, experiment_slug: str):
    """View a single research experiment with findings."""
    experiment_dir = RESEARCH_DIR / experiment_slug

    if not experiment_dir.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Load findings.md
    findings_path = experiment_dir / "findings.md"
    if not findings_path.exists():
        raise HTTPException(status_code=404, detail="Findings not found")

    findings_text = findings_path.read_text()

    # Strip YAML frontmatter before rendering
    frontmatter, findings_markdown = parse_yaml_frontmatter(findings_text)
    findings_html = render_markdown(findings_markdown)

    # Parse metadata
    experiments = parse_research_folder(RESEARCH_DIR)
    experiment = next((e for e in experiments if e.slug == experiment_slug), None)

    return templates.TemplateResponse(
        "research_detail.html",
        {
            "request": request,
            "experiment": experiment,
            "findings_html": findings_html,
        },
    )


@app.get("/research/{experiment_slug}/download")
async def download_research_data(experiment_slug: str):
    """Download all research data as a zip file."""
    experiment_dir = RESEARCH_DIR / experiment_slug

    if not experiment_dir.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Create in-memory zip file
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Files to include (order matters for readability)
        files_to_include = [
            "README.md",
            "config.json",
            "dilemmas.json",
            "judgements.json",
            "analyze.py",
        ]

        # Add individual files
        for filename in files_to_include:
            file_path = experiment_dir / filename
            if file_path.exists():
                zip_file.write(file_path, arcname=filename)

        # Add data/ directory contents
        data_dir = experiment_dir / "data"
        if data_dir.exists() and data_dir.is_dir():
            for file_path in data_dir.rglob("*"):
                if file_path.is_file():
                    # Preserve directory structure within zip
                    arcname = file_path.relative_to(experiment_dir)
                    zip_file.write(file_path, arcname=str(arcname))

        # Add values/ directory if exists
        values_dir = experiment_dir / "values"
        if values_dir.exists() and values_dir.is_dir():
            for file_path in values_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(experiment_dir)
                    zip_file.write(file_path, arcname=str(arcname))

    # Seek to beginning of buffer
    zip_buffer.seek(0)

    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={experiment_slug}.zip"
        },
    )


# ============================================================================
# PROTECTED API ROUTES
# ============================================================================


@app.post("/api/generate", response_model=Dilemma, dependencies=[Depends(verify_api_key)])
async def generate_dilemma(req: GenerateRequest):
    """Generate a new dilemma (protected endpoint).

    Requires API key in X-API-Key header.

    Example:
        curl -X POST https://values-md-dilemmas.fly.dev/api/generate \\
             -H "X-API-Key: your-api-key" \\
             -H "Content-Type: application/json" \\
             -d '{"difficulty": 7, "prompt_version": "v8_concise"}'
    """
    generator = DilemmaGenerator(
        prompt_version=req.prompt_version,
    )

    try:
        dilemma = await generator.generate_random(
            difficulty=req.difficulty,
            num_actors=req.num_actors,
            num_stakes=req.num_stakes,
            add_variables=req.add_variables,
        )

        # Save to database
        db = get_database()
        async for session in db.get_session():
            db_dilemma = DilemmaDB.from_domain(dilemma)
            session.add(db_dilemma)
            await session.commit()

        await db.close()

        return dilemma

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get(
    "/api/dilemmas",
    response_model=DilemmaListResponse,
    dependencies=[Depends(verify_api_key)],
)
async def list_dilemmas_protected(
    limit: int = Query(50, ge=1, le=500, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    difficulty_min: int | None = Query(None, ge=1, le=10, description="Minimum difficulty"),
    difficulty_max: int | None = Query(None, ge=1, le=10, description="Maximum difficulty"),
    tags: str | None = Query(None, description="Comma-separated tags to filter by"),
    created_by: str | None = Query(None, description="Filter by creator"),
    search: str | None = Query(None, description="Search in title and situation"),
    sort: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc or desc)"),
):
    """List and search dilemmas with filtering (protected endpoint).

    Requires API key in X-API-Key header.

    Example:
        curl https://values-md-dilemmas.fly.dev/api/dilemmas?limit=10&difficulty_min=7 \\
             -H "X-API-Key: your-api-key"
    """
    db = get_database()

    async for session in db.get_session():
        # Build query
        statement = select(DilemmaDB)

        # Apply filters
        if difficulty_min is not None:
            statement = statement.where(DilemmaDB.difficulty_intended >= difficulty_min)
        if difficulty_max is not None:
            statement = statement.where(DilemmaDB.difficulty_intended <= difficulty_max)
        if created_by is not None:
            statement = statement.where(DilemmaDB.created_by == created_by)

        # Tag filtering (JSON contains)
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            # For each tag, filter where tags_json contains it
            for tag in tag_list:
                statement = statement.where(DilemmaDB.tags_json.contains(f'"{tag}"'))

        # Search in title
        if search:
            statement = statement.where(
                or_(
                    DilemmaDB.title.contains(search),
                    DilemmaDB.data.contains(search),  # Search in JSON data
                )
            )

        # Count total before pagination
        count_statement = statement
        count_result = await session.execute(count_statement)
        total = len(count_result.scalars().all())

        # Apply sorting
        if hasattr(DilemmaDB, sort):
            sort_column = getattr(DilemmaDB, sort)
            if order == "desc":
                statement = statement.order_by(sort_column.desc())
            else:
                statement = statement.order_by(sort_column.asc())

        # Apply pagination
        statement = statement.offset(offset).limit(limit)

        # Execute
        result = await session.execute(statement)
        dilemmas_db = result.scalars().all()
        dilemmas = [db_dilemma.to_domain() for db_dilemma in dilemmas_db]

    await db.close()

    return DilemmaListResponse(
        items=dilemmas,
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get("/api/stats", response_model=StatsResponse, dependencies=[Depends(verify_api_key)])
async def get_stats():
    """Get database statistics (protected endpoint).

    Requires API key in X-API-Key header.
    """
    db = get_database()

    async for session in db.get_session():
        # Count dilemmas
        dilemma_count_result = await session.execute(select(DilemmaDB))
        dilemmas_count = len(dilemma_count_result.scalars().all())

        # Count judgements
        judgement_count_result = await session.execute(select(JudgementDB))
        judgements_count = len(judgement_count_result.scalars().all())

        # Get unique models tested
        judgement_result = await session.execute(select(JudgementDB))
        judgements = [j.to_domain() for j in judgement_result.scalars().all()]
        models_tested = list(set(j.model for j in judgements if j.model))

        # Get difficulty distribution
        dilemma_result = await session.execute(select(DilemmaDB))
        all_dilemmas = dilemma_result.scalars().all()
        difficulty_distribution = {}
        for dilemma_db in all_dilemmas:
            diff = dilemma_db.difficulty_intended
            difficulty_distribution[diff] = difficulty_distribution.get(diff, 0) + 1

    await db.close()

    # Count research experiments
    experiments_count = 0
    if RESEARCH_DIR.exists():
        experiments_count = len(parse_research_folder(RESEARCH_DIR))

    return StatsResponse(
        dilemmas_count=dilemmas_count,
        judgements_count=judgements_count,
        experiments_count=experiments_count,
        models_tested=sorted(models_tested),
        difficulty_distribution=difficulty_distribution,
    )
