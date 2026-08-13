from typing import List
from fastapi import APIRouter, HTTPException, status, UploadFile, File

from app.schemas.rag import AskRequest, AskResponse, IngestResponse
from app.services.vector_store_service import vector_store_service
from app.services.orchestrator_agent import orchestrator_agent

router = APIRouter(prefix="/api/rag", tags=["RAG Services"])

ALLOWED_MIME_TYPES = {"text/plain", "application/pdf", "image/png", "image/jpeg"}


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        return orchestrator_agent.process_query(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/ingest", response_model=IngestResponse)
def ingest():
    try:
        res = vector_store_service.ingest_documents(force_rebuild=True)
        if res["status"] == "error":
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ingestion failed.")
        return IngestResponse(status=res["status"], document_count=res["document_count"], chunk_count=res["chunk_count"])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {file.content_type}. Only TXT, PDF, PNG, and JPG files are supported."
        )
    try:
        file_bytes = await file.read()
        orchestrator_agent.process_incoming_file(file_bytes, file.filename, file.content_type)
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sources", response_model=List[str])
def get_sources():
    try:
        return vector_store_service.get_unique_sources()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
