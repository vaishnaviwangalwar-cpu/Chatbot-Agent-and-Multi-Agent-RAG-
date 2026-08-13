import os
import glob
import logging
from typing import List, Dict, Any

import chromadb

from app.config import settings
from app.genai_client import get_genai_client
from app.schemas.rag import RetrievedChunkInfo

logger = logging.getLogger(__name__)

# Root directory for seed policy .txt files
_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "sample_docs")

# Chunks shorter than this are title/header lines with no real content — skip them
_MIN_CHUNK_LENGTH = 80


class VectorStoreService:
    """Manages document chunking, Gemini embedding generation, and ChromaDB vector queries."""

    def __init__(self):
        self._chroma_client = None
        self._collection = None
        self.docs_dir = _DOCS_DIR

    def get_collection(self):
        """Lazily connects to persistent ChromaDB and opens the policy collection."""
        if self._collection is None:
            self._chroma_client = chromadb.PersistentClient(path=settings.chroma_path)
            self._collection = self._chroma_client.get_or_create_collection(
                name="campus_policies",
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def load_documents(self) -> List[Dict[str, str]]:
        """Reads every .txt policy document from the sample_docs folder."""
        documents = []
        for path in sorted(glob.glob(os.path.join(self.docs_dir, "*.txt"))):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    documents.append({"source": os.path.basename(path), "text": f.read().strip()})
            except Exception as e:
                logger.error(f"Failed to read document {path}: {e}")
        return documents

    def chunk_text(self, text: str) -> List[str]:
        """Splits policy text into paragraph chunks on double newlines, discarding short title/header lines."""
        return [p.strip() for p in text.split("\n\n") if len(p.strip()) >= _MIN_CHUNK_LENGTH]

    def _embed(self, texts: List[str]) -> List[list]:
        """Generates Gemini embeddings for a list of text chunks in batches of 100."""
        embeddings = []
        client = get_genai_client()
        for i in range(0, len(texts), 100):
            batch = texts[i: i + 100]
            res = client.models.embed_content(model=settings.embedding_model, contents=batch)
            embeddings.extend([emb.values for emb in res.embeddings])
        return embeddings

    def ingest_documents(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Loads policy documents, chunks, embeds, and stores them in ChromaDB."""
        collection = self.get_collection()
        current_count = collection.count()

        if current_count > 0 and not force_rebuild:
            logger.info("Vector store already populated. Skipping auto-ingestion.")
            return {"status": "skipped", "document_count": len(glob.glob(os.path.join(self.docs_dir, "*.txt"))), "chunk_count": current_count}

        logger.info("Rebuilding vector store...")
        documents = self.load_documents()
        if not documents:
            return {"status": "error", "document_count": 0, "chunk_count": 0}

        if force_rebuild:
            try:
                self._chroma_client.delete_collection("campus_policies")
            except Exception:
                pass
            self._collection = self._chroma_client.get_or_create_collection(
                name="campus_policies",
                metadata={"hnsw:space": "cosine"}
            )
            collection = self._collection

        all_chunks, all_ids, all_metadatas = [], [], []
        for doc in documents:
            for i, chunk in enumerate(self.chunk_text(doc["text"])):
                all_chunks.append(chunk)
                all_ids.append(f"{doc['source']}-{i}")
                all_metadatas.append({"source": doc["source"]})

        collection.add(ids=all_ids, embeddings=self._embed(all_chunks), documents=all_chunks, metadatas=all_metadatas)
        return {"status": "success", "document_count": len(documents), "chunk_count": collection.count()}

    def search(self, query: str, top_k: int = 3) -> List[RetrievedChunkInfo]:
        """Embeds the query and performs cosine similarity search over ChromaDB."""
        collection = self.get_collection()
        query_vector = self._embed([query])[0]
        results = collection.query(query_embeddings=[query_vector], n_results=top_k)

        if not results or not results["documents"]:
            return []

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0] if "distances" in results else [None] * len(docs)

        return [
            RetrievedChunkInfo(text=doc, source=meta.get("source", "unknown"), score=float(dist) if dist is not None else None)
            for doc, meta, dist in zip(docs, metas, dists)
        ]

    def get_unique_sources(self) -> List[str]:
        """Returns all unique document source names currently indexed in ChromaDB."""
        try:
            results = self.get_collection().get(include=["metadatas"])
            sources = {meta["source"] for meta in results.get("metadatas", []) if meta and "source" in meta}
            return sorted(sources)
        except Exception as e:
            logger.error(f"Failed to fetch unique sources: {e}")
            return [doc["source"] for doc in self.load_documents()]

    def add_document_text(self, filename: str, text: str) -> None:
        """Chunks, embeds, and indexes a dynamically uploaded document into ChromaDB."""
        collection = self.get_collection()
        chunks = self.chunk_text(text)
        ids = [f"{filename}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename}] * len(chunks)
        collection.add(ids=ids, embeddings=self._embed(chunks), documents=chunks, metadatas=metadatas)


vector_store_service = VectorStoreService()
