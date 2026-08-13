from typing import List, Optional
from pydantic import BaseModel


class AskRequest(BaseModel):
    """Grounded RAG query request payload."""
    question: str
    top_k: Optional[int] = None


class RetrievedChunkInfo(BaseModel):
    """Details about a matching chunk retrieved from the vector store."""
    text: str
    source: str
    score: Optional[float] = None


class AskResponse(BaseModel):
    """Response payload for RAG question answering."""
    question: str
    answer: str
    sources: List[str]
    retrieved_chunks: List[RetrievedChunkInfo]


class IngestResponse(BaseModel):
    """Response returned after processing and embedding documents."""
    status: str
    document_count: int
    chunk_count: int


class HealthResponse(BaseModel):
    """Server health status report including metadata."""
    status: str
    model: str
    embedding_model: str
    chunk_count: int
