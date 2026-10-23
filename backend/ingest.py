import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from backend.config import settings

class LocalChromaEmbeddings(Embeddings):
    """LangChain-compatible wrapper for ChromaDB's default ONNX all-MiniLM-L6-v2 embedding model."""

    def __init__(self):
        self._ef = DefaultEmbeddingFunction()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raw = self._ef(texts)
        return [[float(v) for v in row] for row in raw]

    def embed_query(self, text: str) -> List[float]:
        raw = self._ef([text])[0]
        return [float(v) for v in raw]


class SafeGeminiOrLocalEmbeddings(Embeddings):
    """Embeddings provider that attempts Gemini first and falls back to Local Chroma ONNX on any error."""

    def __init__(self, gemini_embeddings: Optional[Embeddings] = None):
        self._gemini = gemini_embeddings
        self._local = LocalChromaEmbeddings()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._gemini is not None:
            try:
                return self._gemini.embed_documents(texts)
            except Exception as e:
                print(f"[WARN] Gemini embed_documents failed ({e}). Falling back to local embeddings.")
        return self._local.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        if self._gemini is not None:
            try:
                return self._gemini.embed_query(text)
            except Exception as e:
                print(f"[WARN] Gemini embed_query failed ({e}). Falling back to local embeddings.")
        return self._local.embed_query(text)


def get_embedding_model(provider: Optional[str] = None) -> Tuple[Embeddings, str]:
    """
    Returns the appropriate embedding function based on configuration.
    Defaults to Gemini if configured, otherwise falls back gracefully to Local Chroma ONNX.
    """
    chosen_provider = (provider or settings.EMBEDDING_PROVIDER).lower()

    if chosen_provider == "gemini":
        if settings.is_gemini_key_configured and settings.GOOGLE_API_KEY.startswith("AIzaSy"):
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                gemini_emb = GoogleGenerativeAIEmbeddings(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    google_api_key=settings.GOOGLE_API_KEY
                )
                return SafeGeminiOrLocalEmbeddings(gemini_emb), "gemini"
            except Exception as e:
                print(f"[WARN] Failed to initialize Gemini embeddings ({e}). Falling back to local embeddings.")
        else:
            print("[INFO] Google AI Studio key (starting with AIzaSy) not set. Using local Chroma ONNX embeddings.")

    return LocalChromaEmbeddings(), "local"



def extract_section_headers_from_page(page_text: str) -> List[str]:
    """
    Identifies official manual section and chapter titles from page text.
    Examples matched:
      - CHAPTER – 2 IMPORTANT DEFINITIONS
      - 07.02 Extension of copyright (renewal)
      - 03.08 Fee
      - 03.06.02.06 Classification of designs
      - ANNEXURE I IMPORTANT CASE LAWS
    """
    headers = []
    pattern = re.compile(
        r'^(?:CHAPTER\s*[\d–\-]+[^\n]*|\d{2}\.\d{2}(?:\.\d{2})*\s+[^\n]+|ANNEXURE\s*[-–I|V]+[^\n]*)',
        re.IGNORECASE
    )
    for line in page_text.split("\n"):
        clean = line.strip()
        if pattern.match(clean) and len(clean) > 4:
            headers.append(clean)
    return headers


def load_pdf_documents(pdf_path: str) -> List[Document]:
    """
    Loads and validates the PDF using PyPDFLoader.
    Normalizes zero-indexed pages to 1-indexed document page numbers.
    Tracks active chapter/section metadata across consecutive pages.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
    if path.stat().st_size == 0:
        raise ValueError(f"PDF file at {pdf_path} is empty (0 bytes).")

    loader = PyPDFLoader(str(path))
    raw_pages = loader.load()

    if not raw_pages:
        raise ValueError(f"No pages could be extracted from {pdf_path}.")

    total_characters = 0
    non_empty_pages = 0
    enriched_pages: List[Document] = []
    current_section = "Preface / General"

    source_filename = path.name

    for idx, page_doc in enumerate(raw_pages):
        raw_text = page_doc.page_content or ""
        total_characters += len(raw_text.strip())
        if len(raw_text.strip()) > 20:
            non_empty_pages += 1

        # Look for section headers on this page
        headers = extract_section_headers_from_page(raw_text)
        if headers:
            current_section = headers[0]

        # 1-indexed page normalization
        page_number = idx + 1

        metadata = {
            "source": source_filename,
            "page": page_number,
            "section": current_section,
            "raw_page_index": idx
        }

        enriched_pages.append(Document(page_content=raw_text, metadata=metadata))

    if total_characters == 0 or non_empty_pages == 0:
        raise ValueError(
            f"PDF extraction yielded no readable text from {len(raw_pages)} pages. "
            "The document might be scanned images requiring OCR."
        )

    print(f"[INGEST] Loaded {len(enriched_pages)} pages ({non_empty_pages} non-empty, {total_characters} characters total).")
    return enriched_pages


def chunk_documents(documents: List[Document], chunk_size: int = 900, chunk_overlap: int = 150) -> List[Document]:
    """
    Splits documents into coherent chunks using RecursiveCharacterTextSplitter.
    Preserves and enriches metadata with unique chunk identifiers and section titles.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )

    chunks: List[Document] = []
    chunk_counter_per_page = {}

    for doc in documents:
        page_num = doc.metadata.get("page", 1)
        sub_chunks = text_splitter.split_documents([doc])

        for sub_chunk in sub_chunks:
            # Check if this specific chunk contains a more specific section header
            specific_headers = extract_section_headers_from_page(sub_chunk.page_content)
            chunk_section = specific_headers[0] if specific_headers else doc.metadata.get("section", "General")

            c_idx = chunk_counter_per_page.get(page_num, 0) + 1
            chunk_counter_per_page[page_num] = c_idx

            source = doc.metadata.get("source", "designs_manual.pdf")
            chunk_id = f"{source}_p{page_num}_c{c_idx}"

            sub_chunk.metadata = {
                "source": source,
                "page": int(page_num),
                "section": chunk_section,
                "chunk_id": chunk_id
            }
            chunks.append(sub_chunk)

    print(f"[INGEST] Generated {len(chunks)} chunks from {len(documents)} pages.")
    return chunks


def build_vector_store(
    chunks: List[Document],
    rebuild: bool = False,
    provider: Optional[str] = None
) -> Chroma:
    """
    Indexes chunks into persistent ChromaDB storage.
    Supports deterministic rebuild.
    """
    persist_dir = Path(settings.CHROMA_PERSIST_DIRECTORY)
    collection_name = settings.CHROMA_COLLECTION_NAME

    if rebuild and persist_dir.exists():
        print(f"[INGEST] Rebuild requested: Removing existing Chroma database at {persist_dir}...")
        shutil.rmtree(persist_dir, ignore_errors=True)

    persist_dir.mkdir(parents=True, exist_ok=True)

    embeddings, active_provider = get_embedding_model(provider)
    print(f"[INGEST] Using embedding provider: {active_provider}")

    # Initialize Chroma vector store
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(persist_dir)
    )

    # Ingest in batches to handle memory and progress cleanly
    batch_size = 100
    total = len(chunks)
    ids = [c.metadata["chunk_id"] for c in chunks]

    for i in range(0, total, batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]
        vector_store.add_documents(documents=batch_chunks, ids=batch_ids)
        print(f"[INGEST] Indexed chunks {i + 1} to {min(i + batch_size, total)} of {total}...")

    print(f"[INGEST] Completed vector indexing in collection '{collection_name}' at {persist_dir}.")
    return vector_store


def run_ingestion(
    pdf_path: Optional[str] = None,
    rebuild: bool = False,
    provider: Optional[str] = None
) -> int:
    """Main ingestion pipeline runner."""
    target_pdf = pdf_path or settings.DEFAULT_PDF_PATH
    print(f"[INGEST] Starting ingestion pipeline for: {target_pdf}")

    documents = load_pdf_documents(target_pdf)
    chunks = chunk_documents(
        documents,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    build_vector_store(chunks, rebuild=rebuild, provider=provider)
    print("[INGEST] Pipeline finished successfully.")
    return len(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Designs Practice & Procedure Manual into ChromaDB.")
    parser.add_argument("--pdf", type=str, default=None, help="Path to the PDF document.")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the vector store from scratch.")
    parser.add_argument("--provider", type=str, choices=["gemini", "local"], default=None, help="Embedding provider.")

    args = parser.parse_args()
    try:
        run_ingestion(pdf_path=args.pdf, rebuild=args.rebuild, provider=args.provider)
    except Exception as exc:
        print(f"[ERROR] Ingestion failed: {exc}", file=sys.stderr)
        sys.exit(1)
