import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.schemas import AskRequest, AskResponse, HealthResponse, RootStatusResponse
from backend.rag import get_rag_pipeline

# Configure server logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("designs-law-assistant")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management for shared resources."""
    logger.info("Starting Designs Law Assistant API server...")
    logger.info(f"Persistent ChromaDB directory: {settings.CHROMA_PERSIST_DIRECTORY}")
    logger.info(f"Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    logger.info(f"Gemini API Key configured: {settings.is_gemini_key_configured}")
    # Pre-warm RAG pipeline
    try:
        pipeline = get_rag_pipeline()
        logger.info("RAG pipeline pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"RAG pipeline deferred initialization: {e}")
    yield
    logger.info("Shutting down Designs Law Assistant API server...")

app = FastAPI(
    title="Designs Law Assistant API",
    description="Document-grounded RAG API for Manual of Designs Practice & Procedure (CGPDTM, IP India)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get(
    "/",
    response_model=RootStatusResponse,
    summary="Application Root Status",
    tags=["System"]
)
async def root() -> RootStatusResponse:
    """Returns concise application metadata and operational status."""
    return RootStatusResponse()

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health & Readiness Check",
    tags=["System"]
)
async def health() -> HealthResponse:
    """
    Checks operational health and ChromaDB initialization status.
    Never exposes API keys or internal secrets.
    """
    db_ready = settings.chroma_db_exists
    status_str = "healthy" if db_ready else "degraded (database unindexed)"
    provider_str = "gemini" if settings.is_gemini_key_configured else "local"

    return HealthResponse(
        status=status_str,
        database_initialized=db_ready,
        embedding_provider=provider_str,
        model=settings.GEMINI_MODEL
    )

@app.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask Document-Grounded Question",
    tags=["RAG Assistant"]
)
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Answers user questions strictly grounded in the Manual of Designs Practice & Procedure.
    Returns exact 'Not found' with empty citations if evidence is insufficient.
    """
    if not settings.chroma_db_exists:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The vector database has not been initialized. Run 'python -m backend.ingest --pdf data/designs_manual.pdf' first."
        )

    try:
        pipeline = get_rag_pipeline()
        response = pipeline.answer_question(request.question)
        return response
    except Exception as exc:
        logger.error(f"Error processing question: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the request."
        )

# Mount frontend static files for direct browser access at /app
frontend_dir = settings.BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
