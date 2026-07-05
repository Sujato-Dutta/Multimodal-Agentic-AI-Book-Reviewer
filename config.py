from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Deployment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # LLM
    MODEL_NAME: str = "gemini-3.1-flash-lite"
    GOOGLE_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2048

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = "ledgera-books"
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_DIMENSION: int = 384

    # Retrieval
    RETRIEVAL_TOP_K: int = 10
    RERANK_TOP_K: int = 5
    RRF_K: int = 60
    ALLOWED_DOMAINS: List[str] = [
        "books.google.com",
        "openlibrary.org",
        "goodreads.com",
        "amazon.com",
        "librarything.com",
    ]
    GOOGLE_BOOKS_API_URL: str = "https://www.googleapis.com/books/v1/volumes"
    OPEN_LIBRARY_API_URL: str = "https://openlibrary.org"

    # Vision
    MAX_IMAGE_SIZE_MB: int = 10

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Monitoring
    ENABLE_METRICS: bool = True

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # Evals
    EVAL_DATA_PATH: str = "evals/test_cases.json"

    # Source reliability weights
    SOURCE_WEIGHTS: dict = {
        "books.google.com": 0.95,
        "openlibrary.org": 0.90,
        "goodreads.com": 0.85,
        "amazon.com": 0.80,
        "librarything.com": 0.75,
    }

    # Guardrails
    MIN_CONFIDENCE_THRESHOLD: float = 0.3
    MIN_CITATIONS_REQUIRED: int = 2
    SPOILER_KEYWORDS: List[str] = [
        "ending", "dies", "twist", "reveals", "turns out",
        "killed", "murderer", "plot twist", "spoiler",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
