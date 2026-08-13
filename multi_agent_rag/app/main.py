import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.rag_router import router as rag_router
from app.schemas.rag import HealthResponse
from app.services.vector_store_service import vector_store_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing vector database index...")
    try:
        vector_store_service.ingest_documents(force_rebuild=False)
    except Exception as e:
        logger.error(f"Startup document indexing failed: {str(e)}")
    yield


app = FastAPI(title="Multi-Agent Policy Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router)


@app.get("/health", response_model=HealthResponse)
def health():
    try:
        count = vector_store_service.get_collection().count()
    except Exception:
        count = 0
    return HealthResponse(
        status="healthy",
        model=settings.gemini_model,
        embedding_model=settings.embedding_model,
        chunk_count=count
    )


# Mount static frontend assets (must be last)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
