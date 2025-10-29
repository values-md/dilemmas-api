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
from sqlalchemy import func
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


class HumanJudgementItem(BaseModel):
    """Single human judgement submission."""

    dilemma_id: str
    choice_id: str
    confidence: float | None = Field(None, ge=0.0, le=10.0, description="Confidence (0-10)")
    reasoning: str = Field("", description="Optional explanation")
    response_time_ms: int | None = Field(None, description="Time taken to decide")
    rendered_situation: str = Field(..., description="Actual text shown to user")
    variable_values: dict[str, str] | None = Field(None, description="Variable substitutions used")
    modifier_indices: list[int] | None = Field(None, description="Which modifiers were applied")


class HumanDemographics(BaseModel):
    """Optional demographic information."""

    age: int | None = Field(None, ge=1, le=120)
    gender: str | None = None
    education_level: str | None = None
    country: str | None = None
    culture: str | None = None
    professional_background: str | None = None
    device_type: str | None = None


class SubmitJudgementsRequest(BaseModel):
    """Request to submit a batch of human judgements."""

    participant_id: str = Field(..., description="Anonymous participant UUID from frontend")
    demographics: HumanDemographics | None = None
    judgements: list[HumanJudgementItem]


class SubmitJudgementsResponse(BaseModel):
    """Response after submitting judgements."""

    success: bool
    judgement_ids: list[str]
    message: str | None = None


# ============================================================================
# PUBLIC ROUTES - Dilemma Browser
# ============================================================================


@app.get("/")
async def root():
    """Redirect root to research page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/research")


@app.get("/dilemmas", response_class=HTMLResponse)
async def list_dilemmas(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    search: str | None = Query(None, description="Search in title and situation"),
    collection: str | None = Query(None, description="Filter by collection"),
    difficulty: int | None = Query(None, ge=1, le=10, description="Filter by difficulty"),
    institution_type: str | None = Query(None, description="Filter by institution type"),
    domain: str | None = Query(None, description="Filter by domain"),
    tag: str | None = Query(None, description="Filter by tag"),
):
    """List all dilemmas with pagination and search."""
    db = get_database()

    async for session in db.get_session():
        # Build query
        statement = select(DilemmaDB)

        # Apply filters
        if search:
            statement = statement.where(
                or_(
                    DilemmaDB.title.contains(search),
                    DilemmaDB.data.contains(search),
                )
            )
        if collection:
            statement = statement.where(DilemmaDB.collection == collection)
        if difficulty:
            statement = statement.where(DilemmaDB.difficulty_intended == difficulty)
        if institution_type:
            statement = statement.where(
                func.json_extract(DilemmaDB.data, '$.institution_type') == institution_type
            )
        if domain:
            statement = statement.where(
                func.json_extract(DilemmaDB.data, '$.seed_components.domain') == domain
            )
        if tag:
            statement = statement.where(DilemmaDB.tags_json.contains(f'"{tag}"'))

        # Count total (before pagination)
        count_result = await session.execute(statement)
        total = len(count_result.scalars().all())

        # Apply pagination
        offset = (page - 1) * limit
        statement = statement.order_by(DilemmaDB.created_at.desc()).offset(offset).limit(limit)

        result = await session.execute(statement)
        dilemmas_db = result.scalars().all()

        # Convert to domain models
        dilemmas = [db_dilemma.to_domain() for db_dilemma in dilemmas_db]

        # Get available collections for filter dropdown
        collections_statement = (
            select(DilemmaDB.collection)
            .where(DilemmaDB.collection.is_not(None))
            .distinct()
            .order_by(DilemmaDB.collection)
        )
        collections_result = await session.execute(collections_statement)
        available_collections = [c for c in collections_result.scalars().all() if c]

    await db.close()

    # Calculate pagination info
    total_pages = (total + limit - 1) // limit  # Ceiling division
    has_prev = page > 1
    has_next = page < total_pages

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "dilemmas": dilemmas,
            "count": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "search": search or "",
            "collection": collection or "",
            "difficulty": difficulty,
            "institution_type": institution_type or "",
            "domain": domain or "",
            "tag": tag or "",
            "available_collections": available_collections,
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
async def list_judgements(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    search: str | None = Query(None, description="Search in reasoning and choice"),
    experiment_id: str | None = Query(None, description="Filter by experiment ID"),
    model: str | None = Query(None, description="Filter by model"),
):
    """List all judgements with pagination and search."""
    db = get_database()

    async for session in db.get_session():
        # Build query
        statement = select(JudgementDB)

        # Apply filters
        if search:
            statement = statement.where(
                or_(
                    JudgementDB.data.contains(search),
                )
            )
        if experiment_id:
            statement = statement.where(JudgementDB.experiment_id == experiment_id)
        if model:
            statement = statement.where(JudgementDB.judge_id == model)

        # Count total (before pagination)
        count_result = await session.execute(statement)
        total = len(count_result.scalars().all())

        # Apply pagination
        offset = (page - 1) * limit
        statement = statement.order_by(JudgementDB.created_at.desc()).offset(offset).limit(limit)

        result = await session.execute(statement)
        judgements_db = result.scalars().all()

        # Convert to domain models
        judgements = [jdb.to_domain() for jdb in judgements_db]

        # Also load dilemmas to show titles
        dilemma_ids = [j.dilemma_id for j in judgements]
        if dilemma_ids:
            dilemma_statement = select(DilemmaDB).where(DilemmaDB.id.in_(dilemma_ids))
            dilemma_result = await session.execute(dilemma_statement)
            dilemmas_db = {d.id: d.to_domain() for d in dilemma_result.scalars().all()}
        else:
            dilemmas_db = {}

        # Get available experiment IDs and models for filters
        experiments_statement = (
            select(JudgementDB.experiment_id)
            .where(JudgementDB.experiment_id.is_not(None))
            .distinct()
            .order_by(JudgementDB.experiment_id.desc())
            .limit(20)
        )
        experiments_result = await session.execute(experiments_statement)
        available_experiments = [e for e in experiments_result.scalars().all() if e]

        models_statement = (
            select(JudgementDB.judge_id)
            .where(JudgementDB.judge_type == "ai")
            .distinct()
            .order_by(JudgementDB.judge_id)
        )
        models_result = await session.execute(models_statement)
        available_models = [m for m in models_result.scalars().all() if m]

    await db.close()

    # Calculate pagination info
    total_pages = (total + limit - 1) // limit  # Ceiling division
    has_prev = page > 1
    has_next = page < total_pages

    return templates.TemplateResponse(
        "judgements.html",
        {
            "request": request,
            "judgements": judgements,
            "dilemmas": dilemmas_db,
            "count": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "search": search or "",
            "experiment_id": experiment_id or "",
            "model": model or "",
            "available_experiments": available_experiments,
            "available_models": available_models,
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
    collection: str | None = Query(None, description="Filter by collection name"),
    batch_id: str | None = Query(None, description="Filter by batch ID"),
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
        if collection is not None:
            statement = statement.where(DilemmaDB.collection == collection)
        if batch_id is not None:
            statement = statement.where(DilemmaDB.batch_id == batch_id)

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


# ============================================================================
# HUMAN TESTING API - Public endpoints for frontend integration
# ============================================================================


@app.get("/api/collections/{collection_name}/dilemmas", response_model=list[Dilemma])
async def get_collection_dilemmas(collection_name: str):
    """Get all dilemmas in a specific collection (public endpoint).

    Use case: Frontend fetches bench-1 test set for human testing.

    Args:
        collection_name: Name of the collection (e.g., 'bench-1')

    Returns:
        List of dilemmas with all fields (choices, variables, modifiers, tools)
    """
    db = get_database()

    async for session in db.get_session():
        result = await session.execute(
            select(DilemmaDB).where(DilemmaDB.collection == collection_name)
        )
        db_dilemmas = result.scalars().all()

        if not db_dilemmas:
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")

        dilemmas = [d.to_domain() for d in db_dilemmas]

    await db.close()
    return dilemmas


@app.post("/api/judgements", response_model=SubmitJudgementsResponse, dependencies=[Depends(verify_api_key)])
async def submit_human_judgements(request: SubmitJudgementsRequest):
    """Submit a batch of human judgements (public endpoint).

    Use case: Frontend submits user's completed dilemma test.

    Args:
        request: Batch of judgements with participant info and demographics

    Returns:
        Success status and list of created judgement IDs
    """
    from dilemmas.models.judgement import Judgement, HumanJudgeDetails
    import hashlib

    db = get_database()
    judgement_ids = []
    errors = []

    # Convert demographics to dict for HumanJudgeDetails
    demographics_dict = request.demographics.model_dump() if request.demographics else {}

    async for session in db.get_session():
        for item in request.judgements:
            try:
                # Validate dilemma exists
                result = await session.execute(
                    select(DilemmaDB).where(DilemmaDB.id == item.dilemma_id)
                )
                dilemma_db = result.scalar_one_or_none()

                if not dilemma_db:
                    errors.append(f"Dilemma {item.dilemma_id} not found")
                    continue

                dilemma = dilemma_db.to_domain()

                # Validate choice_id exists
                valid_choice_ids = [c.id for c in dilemma.choices]
                if item.choice_id not in valid_choice_ids:
                    errors.append(f"Invalid choice_id '{item.choice_id}' for dilemma {item.dilemma_id}")
                    continue

                # Generate variation_key
                variation_key = None
                if item.variable_values:
                    sorted_items = sorted(item.variable_values.items())
                    key_str = "|".join(f"{k}={v}" for k, v in sorted_items)
                    variation_key = hashlib.md5(key_str.encode()).hexdigest()[:16]

                # Create HumanJudgeDetails
                human_judge = HumanJudgeDetails(
                    participant_id=request.participant_id,
                    **demographics_dict
                )

                # Create Judgement
                judgement = Judgement(
                    dilemma_id=item.dilemma_id,
                    judge_type="human",
                    human_judge=human_judge,
                    mode="theory",  # Humans always use theory mode
                    rendered_situation=item.rendered_situation,
                    variable_values=item.variable_values,
                    modifier_indices=item.modifier_indices,
                    variation_key=variation_key,
                    choice_id=item.choice_id,
                    confidence=item.confidence,
                    reasoning=item.reasoning,
                    response_time_ms=item.response_time_ms,
                )

                # Save to database
                judgement_db = JudgementDB.from_domain(judgement)
                session.add(judgement_db)
                await session.commit()

                judgement_ids.append(judgement.id)

            except Exception as e:
                errors.append(f"Error processing judgement for dilemma {item.dilemma_id}: {str(e)}")
                continue

    await db.close()

    if errors:
        return SubmitJudgementsResponse(
            success=len(judgement_ids) > 0,
            judgement_ids=judgement_ids,
            message=f"Saved {len(judgement_ids)} judgements. Errors: {'; '.join(errors)}"
        )

    return SubmitJudgementsResponse(
        success=True,
        judgement_ids=judgement_ids,
        message=f"Successfully saved {len(judgement_ids)} judgements"
    )


# ============================================================================
# VALUES.md Generation Endpoints
# ============================================================================

class GenerateValuesRequest(BaseModel):
    """Request to generate VALUES.md file."""
    participant_id: str = Field(..., description="Participant identifier")
    model_id: str = Field(
        default="google/gemini-2.5-flash",
        description="LLM model to use for generation"
    )
    force_regenerate: bool = Field(
        default=False,
        description="Force regeneration even if cached version exists"
    )


class GenerateValuesResponse(BaseModel):
    """Response with generated VALUES.md."""
    success: bool
    participant_id: str
    values_md: str | None = None
    from_cache: bool = Field(default=False, description="Whether result is from cache")
    judgement_count: int | None = None
    generated_at: str | None = None
    model_id: str | None = None
    error: str | None = None


@app.post("/api/values/generate", response_model=GenerateValuesResponse, dependencies=[Depends(verify_api_key)])
async def generate_values_md(request: GenerateValuesRequest):
    """Generate VALUES.md file from participant's judgements (protected endpoint).

    Requires minimum 10 judgements. Results are cached permanently until force_regenerate=True.
    """
    from datetime import datetime, timezone
    from dilemmas.models.db import ValuesMdDB
    from dilemmas.services.values_generator import ValuesGenerator

    db = get_database()

    async for session in db.get_session():
        # Check cache first (unless force_regenerate)
        if not request.force_regenerate:
            result = await session.get(ValuesMdDB, request.participant_id)
            if result:
                await db.close()
                return GenerateValuesResponse(
                    success=True,
                    participant_id=request.participant_id,
                    values_md=result.markdown_text,
                    from_cache=True,
                    judgement_count=result.judgement_count,
                    generated_at=result.generated_at.isoformat(),
                    model_id=result.model_id
                )

        # Generate new VALUES.md
        try:
            generator = ValuesGenerator()
            markdown_text, structured_data = await generator.generate(
                session=session,
                participant_id=request.participant_id,
                model_id=request.model_id
            )

            # Save to cache
            now = datetime.now(timezone.utc).replace(tzinfo=None)

            # Check if record exists (for version increment)
            existing = await session.get(ValuesMdDB, request.participant_id)
            version = existing.version + 1 if existing else 1

            # Create or update cache record
            cache_record = ValuesMdDB(
                participant_id=request.participant_id,
                markdown_text=markdown_text,
                structured_json=structured_data.model_dump_json(),
                generated_at=now,
                model_id=request.model_id,
                judgement_count=structured_data.generated_from_count,
                version=version
            )

            # Merge (upsert)
            await session.merge(cache_record)
            await session.commit()

            await db.close()

            return GenerateValuesResponse(
                success=True,
                participant_id=request.participant_id,
                values_md=markdown_text,
                from_cache=False,
                judgement_count=structured_data.generated_from_count,
                generated_at=now.isoformat(),
                model_id=request.model_id
            )

        except ValueError as e:
            # Insufficient judgements
            await db.close()
            return GenerateValuesResponse(
                success=False,
                participant_id=request.participant_id,
                error=str(e)
            )
        except Exception as e:
            # Other errors
            await db.close()
            return GenerateValuesResponse(
                success=False,
                participant_id=request.participant_id,
                error=f"Generation failed: {str(e)}"
            )


@app.get("/api/values/{participant_id}", dependencies=[Depends(verify_api_key)])
async def get_values_md(participant_id: str):
    """Retrieve cached VALUES.md file for a participant (protected endpoint).

    Returns 404 if no VALUES.md has been generated for this participant.
    """
    from dilemmas.models.db import ValuesMdDB

    db = get_database()

    async for session in db.get_session():
        result = await session.get(ValuesMdDB, participant_id)

        if not result:
            await db.close()
            raise HTTPException(
                status_code=404,
                detail=f"No VALUES.md found for participant '{participant_id}'. Generate one first."
            )

        await db.close()

        return GenerateValuesResponse(
            success=True,
            participant_id=participant_id,
            values_md=result.markdown_text,
            from_cache=True,
            judgement_count=result.judgement_count,
            generated_at=result.generated_at.isoformat(),
            model_id=result.model_id
        )
