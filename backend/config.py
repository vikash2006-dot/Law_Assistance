import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    """Application settings loaded from environment variables."""

    BASE_DIR: Path = BASE_DIR

    # Gemini API Settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "").strip()

    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004").strip()
    
    # Embedding provider: "gemini" or "local" (uses Chroma's built-in ONNX all-MiniLM-L6-v2)
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "gemini").strip().lower()

    # ChromaDB Vector Store Settings
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", str(BASE_DIR / "chroma_db"))
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "designs_manual_collection")

    # Ingestion & Chunking Defaults
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "900"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    DEFAULT_PDF_PATH: str = str(BASE_DIR / "data" / "designs_manual.pdf")

    # Retrieval Defaults
    DEFAULT_K: int = int(os.getenv("DEFAULT_K", "4"))
    MAX_QUESTION_LENGTH: int = 500

    # Server & Security
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "*"
    ]

    @property
    def is_gemini_key_configured(self) -> bool:
        """Returns True if a valid Google AI Studio key is configured."""
        if not self.GOOGLE_API_KEY:
            return False
        if "your_gemini_api_key" in self.GOOGLE_API_KEY.lower():
            return False
        return self.GOOGLE_API_KEY.startswith("AIzaSy")


    @property
    def chroma_db_exists(self) -> bool:
        """Checks if the Chroma persist directory exists and has files."""
        db_path = Path(self.CHROMA_PERSIST_DIRECTORY)
        if not db_path.exists():
            return False
        # Chroma creates sqlite or index files inside
        return any(db_path.iterdir())

settings = Settings()
