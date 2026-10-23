import pytest
from backend.rag import RAGPipeline
from backend.retrieval import get_retriever

def test_rag_unsupported_trademark_fee_exact_not_found():
    """Verify trademark fee returns exact 'Not found' with found=False and empty citations."""
    rag = RAGPipeline()
    response = rag.answer_question("What is the government fee to register a trademark?")
    assert response.answer == "Not found"
    assert response.found is False
    assert response.citations == []

def test_rag_unsupported_current_controller_exact_not_found():
    """Verify current Controller General returns exact 'Not found'."""
    rag = RAGPipeline()
    response = rag.answer_question("Who is the current Controller General of Patents?")
    assert response.answer == "Not found"
    assert response.found is False
    assert response.citations == []

def test_rag_q1_copyright_duration_grounded():
    """Verify copyright duration & extension question returns grounded answer with citations."""
    rag = RAGPipeline()
    response = rag.answer_question("How long does a proprietor have copyright in a registered design, and can it be extended?")
    assert response.found is True
    assert "ten" in response.answer.lower() or "10" in response.answer
    assert "five" in response.answer.lower() or "5" in response.answer
    assert len(response.citations) > 0
    # Citations must reference actual pages
    pages = [c.page for c in response.citations]
    assert any(p in [36, 39, 40] for p in pages)

def test_rag_q2_classification_system_grounded():
    """Verify classification system question returns Locarno with citations."""
    rag = RAGPipeline()
    response = rag.answer_question("Which classification system is used to register designs?")
    assert response.found is True
    assert "locarno" in response.answer.lower()
    assert len(response.citations) > 0
    pages = [c.page for c in response.citations]
    assert any(p in [5, 14, 20] for p in pages)

def test_rag_q5_design_fee_grounded():
    """Verify design fee question returns First Schedule citation."""
    rag = RAGPipeline()
    response = rag.answer_question("What is the fee to register a design?")
    assert response.found is True
    assert "first schedule" in response.answer.lower() or "prescribed" in response.answer.lower()
    assert len(response.citations) > 0
    pages = [c.page for c in response.citations]
    assert any(p in [22, 23, 24] for p in pages)
