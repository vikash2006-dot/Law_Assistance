import pytest
from pathlib import Path
from langchain_core.documents import Document
from backend.ingest import (
    load_pdf_documents,
    chunk_documents,
    extract_section_headers_from_page
)

def test_pdf_missing_raises_error(tmp_path):
    """Verify that a missing PDF path raises FileNotFoundError."""
    missing_file = tmp_path / "non_existent.pdf"
    with pytest.raises(FileNotFoundError):
        load_pdf_documents(str(missing_file))

def test_empty_pdf_raises_error(tmp_path):
    """Verify that an empty (0-byte) PDF file raises ValueError."""
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        load_pdf_documents(str(empty_file))

def test_extract_section_headers():
    """Verify that regex extracts chapter and section headers correctly."""
    sample_text = (
        "CHAPTER – 2 IMPORTANT DEFINITIONS\n"
        "Some introductory text here.\n"
        "02.01 General\n"
        "More text.\n"
        "07.02 Extension of copyright (renewal)\n"
    )
    headers = extract_section_headers_from_page(sample_text)
    assert len(headers) >= 3
    assert "CHAPTER – 2 IMPORTANT DEFINITIONS" in headers
    assert "02.01 General" in headers
    assert "07.02 Extension of copyright (renewal)" in headers

def test_chunking_preserves_metadata():
    """Verify chunking maintains 1-indexed page, source, section, and stable IDs."""
    doc = Document(
        page_content="03.08 Fee\na. The fee to be paid in respect of any matter is prescribed in First Schedule." * 10,
        metadata={"source": "designs_manual.pdf", "page": 22, "section": "03.08 Fee"}
    )
    chunks = chunk_documents([doc], chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.metadata["source"] == "designs_manual.pdf"
        assert chunk.metadata["page"] == 22
        assert "Fee" in chunk.metadata["section"]
        assert chunk.metadata["chunk_id"].startswith("designs_manual.pdf_p22_c")
