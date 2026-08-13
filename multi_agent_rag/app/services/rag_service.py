import logging

from app.config import settings
from app.genai_client import get_genai_client
from app.prompts.rag_prompt import PROMPT_TEMPLATE
from app.schemas.rag import AskRequest, AskResponse
from app.services.vector_store_service import vector_store_service

logger = logging.getLogger(__name__)


class RagService:
    """RAG specialist agent: retrieves relevant context chunks and generates a grounded answer."""

    def process_query(self, request: AskRequest) -> AskResponse:
        """Runs the full RAG pipeline: Retrieve → Augment → Generate."""
        top_k = request.top_k or settings.top_k
        logger.info(f"RAG Agent querying: '{request.question}' (Top-K={top_k})")

        # 1. Retrieve — semantic similarity search over ChromaDB chunks
        chunks = vector_store_service.search(request.question, top_k=top_k)

        # 2. Augment — assemble retrieved policy paragraphs into the XML grounding template
        context_str = "\n\n".join(c.text for c in chunks)
        prompt = PROMPT_TEMPLATE.format(context=context_str, question=request.question)

        # 3. Generate — call Gemini with the grounded prompt to produce the final reply
        response = get_genai_client().models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        reply = response.text or "I apologize, but I could not generate a response."
        sources = sorted(set(c.source for c in chunks))

        return AskResponse(
            question=request.question,
            answer=reply,
            sources=sources,
            retrieved_chunks=chunks
        )


rag_service = RagService()
