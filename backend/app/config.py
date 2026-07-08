"""
Configuration module - loads environment variables.
"""
import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "docgen"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # GitHub
    github_token: str = ""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Processing
    max_file_size_kb: int = 500
    max_repo_size_mb: int = 100
    clone_dir: str = "./cloned_repos"

    # Compressor toggle (true = fast ~18 calls, false = per-file ~50+ calls)
    use_compressor: bool = True

    # Background generation
    gen_api_description: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
