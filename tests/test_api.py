import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import settings

client = TestClient(app)

def test_root_endpoint():
    """Verify GET / returns application status information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "Designs Law Assistant"
    assert data["status"] == "operational"
    assert "docs_url" in data

def test_health_endpoint_no_secrets():
    """Verify GET /health returns operational info without leaking keys."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database_initialized" in data
    assert data["database_initialized"] is True
    # Verify no secret credentials in payload
    payload_str = str(data)
    assert settings.GOOGLE_API_KEY not in payload_str or not settings.GOOGLE_API_KEY

def test_ask_valid_grounded_question():
    """Verify POST /ask with a valid question returns 200 and schema."""
    response = client.post("/ask", json={"question": "Which classification system is used to register designs?"})
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Which classification system is used to register designs?"
    assert data["found"] is True
    assert "locarno" in data["answer"].lower()
    assert len(data["citations"]) > 0

def test_ask_unsupported_question_exact_not_found():
    """Verify POST /ask with unsupported question returns exact 'Not found' and empty citations."""
    response = client.post("/ask", json={"question": "What is the government fee to register a trademark?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Not found"
    assert data["found"] is False
    assert data["citations"] == []

def test_ask_empty_question_fails_validation():
    """Verify POST /ask with empty question returns HTTP 422 Unprocessable Entity."""
    response = client.post("/ask", json={"question": "   "})
    assert response.status_code == 422

def test_ask_oversized_question_fails_validation():
    """Verify POST /ask with question exceeding 500 characters returns HTTP 422."""
    oversized = "a" * 501
    response = client.post("/ask", json={"question": oversized})
    assert response.status_code == 422
