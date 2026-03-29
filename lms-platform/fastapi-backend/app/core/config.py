from pydantic_settings import BaseSettings
from pathlib import Path
import os
from typing import Optional, List
from pydantic import ConfigDict

# Define base directory relative to this file (app/core/config.py)
# This points to lms-platform/fastapi-backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")
    PROJECT_NAME: str = "LMS Platform"
    
    # CORS
    # List of origins that are allowed to make cross-origin requests
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Weaviate
    WEAVIATE_URL: str = "http://weaviate:8080"
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Neo4j
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    
    # Use absolute paths for reliability
    CURRICULUM_PDF_PATH: str = str(DATA_DIR / "Comprehensive_Grade_4_English_Curriculum_Design_(Kenya_CBC).pdf")
    FAISS_INDEX_PATH: str = str(DATA_DIR / "faiss_index")

    # LLM Configuration (OpenAI, Groq, OpenRouter, etc.)
    LLM_PROVIDER: str = "openai" # "openai", "groq", "openrouter", "anthropic"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-3.5-turbo" # Default model
    LLM_BASE_URL: Optional[str] = None # Optional custom base URL

    # Monitoring
    SENTRY_DSN: Optional[str] = None


settings = Settings()
