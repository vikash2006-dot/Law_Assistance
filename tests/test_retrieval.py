import pytest
from langchain_core.documents import Document
from backend.retrieval import Retriever

def test_query_normalization():
    """Verify query normalization cleans up extra spaces and returns clean text."""
    query = "   Which   classification   system \n\t is used to  register designs?   "
    clean = Retriever.normalize_query(query)
    assert clean == "Which classification system is used to register designs?"

def test_context_formatting():
    """Verify retrieved chunks are formatted into tagged, clear evidence blocks."""
    docs = [
        Document(
            page_content="Locarno classification system is used for designs.",
            metadata={"source": "designs_manual.pdf", "page": 5, "section": "CHAPTER-1"}
        ),
        Document(
            page_content="Articles are classified into 31 classes.",
            metadata={"source": "designs_manual.pdf", "page": 20, "section": "03.06.02.06 Classification"}
        )
    ]
    context = Retriever.format_context(docs)
    assert "[DOCUMENT CHUNK 1]" in context
    assert "Page: 5" in context
    assert "Locarno classification" in context
    assert "[DOCUMENT CHUNK 2]" in context
    assert "Page: 20" in context

def test_retriever_query_execution():
    """Verify live retriever returns chunks with metadata from existing index."""
    retriever = Retriever()
    docs = retriever.retrieve("classification system", k=2)
    assert len(docs) > 0
    assert "page" in docs[0].metadata
    assert "source" in docs[0].metadata
