import os
import logging

from app.config import settings
from app.genai_client import get_genai_client
from app.prompts.routing_prompt import ROUTING_PROMPT
from app.prompts.chat_prompt import CHAT_PROMPT
from app.schemas.rag import AskRequest, AskResponse
from app.services.parsing_agent import parsing_agent
from app.services.vector_store_service import vector_store_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Central coordinator for the multi-agent pipeline.
    - Classifies user queries via LLM and routes to the appropriate specialist agent.
    - Delegates file parsing to the Parsing Agent and indexes results in ChromaDB.
    """

    def _classify_intent(self, question: str) -> str:
        """Uses Gemini to classify query intent. Returns 'RAG_AGENT' or 'GENERAL_CONVERSATION'."""
        try:
            response = get_genai_client().models.generate_content(
                model=settings.gemini_model,
                contents=ROUTING_PROMPT.format(question=question)
            )
            decision = response.text.strip().upper() if response.text else "RAG_AGENT"
            logger.info(f"Orchestrator routing decision: {decision}")
            return decision
        except Exception as e:
            logger.error(f"Intent classification failed: {e}. Defaulting to RAG_AGENT.")
            return "RAG_AGENT"

    def process_query(self, request: AskRequest) -> AskResponse:
        """
        Entry point for all user queries.
        Classifies intent, then routes to RAG Agent or handles as casual conversation.
        """
        decision = self._classify_intent(request.question)

        if "RAG_AGENT" in decision:
            return rag_service.process_query(request)

        # Handle casual conversation — guide user towards policy questions
        try:
            response = get_genai_client().models.generate_content(
                model=settings.gemini_model,
                contents=CHAT_PROMPT.format(question=request.question)
            )
            answer = response.text or "Hello! How can I help you with campus policies today?"
        except Exception as e:
            logger.error(f"Casual chat response failed: {e}")
            answer = "Hello! How can I help you with campus policies today?"

        return AskResponse(question=request.question, answer=answer, sources=[], retrieved_chunks=[])

    def process_incoming_file(self, file_bytes: bytes, filename: str, mime_type: str) -> None:
        """
        Handles file uploads: delegates parsing to the Parsing Agent,
        persists extracted text to disk, and indexes it in ChromaDB.
        """
        logger.info(f"Orchestrating file upload: {filename} ({mime_type})")

        # 1. Parsing Agent — extract structured text from PDF/image/txt
        parsed_text = parsing_agent.parse_file(file_bytes, mime_type)
        if not parsed_text.strip():
            raise ValueError(f"Could not extract any text content from: {filename}")

        # 2. Persist parsed text to disk so it survives index rebuilds
        base, ext = os.path.splitext(filename)
        save_filename = filename if ext.lower() == ".txt" else f"{base}.txt"
        save_path = os.path.join(vector_store_service.docs_dir, save_filename)
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(parsed_text)
            logger.info(f"Saved parsed text to disk: {save_path}")
        except Exception as e:
            logger.error(f"Failed to save parsed text to disk: {e}")

        # 3. Index parsed text chunks in ChromaDB with Gemini embeddings
        vector_store_service.add_document_text(save_filename, parsed_text)
        logger.info(f"Successfully indexed document: {save_filename}")


orchestrator_agent = OrchestratorAgent()
