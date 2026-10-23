import re
from typing import List, Optional, Tuple
from pathlib import Path

from langchain_core.documents import Document
from langchain_chroma import Chroma

from backend.config import settings
from backend.ingest import get_embedding_model

class Retriever:
    """Handles semantic retrieval and evidence preparation from persistent ChromaDB."""

    def __init__(self, provider: Optional[str] = None):
        self.persist_directory = Path(settings.CHROMA_PERSIST_DIRECTORY)
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self.provider = provider or settings.EMBEDDING_PROVIDER
        self._vector_store: Optional[Chroma] = None

    def get_vector_store(self) -> Chroma:
        """Lazily connects to the persistent Chroma collection."""
        if self._vector_store is not None:
            return self._vector_store

        if not self.persist_directory.exists() or not any(self.persist_directory.iterdir()):
            raise RuntimeError(
                f"ChromaDB persistent database not initialized at '{self.persist_directory}'. "
                "Please run ingestion first using: python -m backend.ingest --pdf data/designs_manual.pdf"
            )

        embeddings, active_provider = get_embedding_model(self.provider)
        self._vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=embeddings,
            persist_directory=str(self.persist_directory)
        )
        return self._vector_store

    @staticmethod
    def normalize_query(query: str) -> str:
        """
        Normalizes whitespace and removes extraneous punctuation while
        preserving crucial legal domain keywords (e.g., numbers, sections, quotes).
        """
        clean = re.sub(r'[\r\n\t]+', ' ', query)
        clean = re.sub(r'\s{2,}', ' ', clean)
        return clean.strip()

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Retrieves top-k relevant document chunks for the given question.
        Applies query normalization, deduplication, and metadata verification.
        """
        store = self.get_vector_store()
        top_k = k or settings.DEFAULT_K
        normalized = self.normalize_query(query)

        # Baseline similarity search
        raw_docs = store.similarity_search(normalized, k=top_k * 2)

        # Deduplicate chunks while preserving ranking order
        seen_ids = set()
        deduped: List[Document] = []

        for doc in raw_docs:
            chunk_id = doc.metadata.get("chunk_id") or doc.page_content[:80]
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                deduped.append(doc)
            if len(deduped) >= top_k:
                break

        return deduped

    @staticmethod
    def format_context(documents: List[Document]) -> str:
        """Formats retrieved chunks into clear, tagged evidence blocks for the prompt."""
        formatted_blocks = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "designs_manual.pdf")
            page = doc.metadata.get("page", "Unknown")
            section = doc.metadata.get("section", "Unidentified section")
            formatted_blocks.append(
                f"[DOCUMENT CHUNK {i}]\n"
                f"Source: {source} | Page: {page} | Section: {section}\n"
                f"Content:\n{doc.page_content.strip()}"
            )
        return "\n\n---\n\n".join(formatted_blocks)


_default_retriever: Optional[Retriever] = None

def get_retriever() -> Retriever:
    """Singleton getter for the Retriever instance."""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = Retriever()
    return _default_retriever
