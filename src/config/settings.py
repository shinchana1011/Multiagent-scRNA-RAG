# src/config/settings.py — central app configuration (Member 4)
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Multiagent scRNA-RAG"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"

    runs_dir: str = "runs"
    upload_dir: str = "data/uploads"

    # LLM (reused from Member 2/3 Ollama setup)
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1"
    llm_methods_section: bool = True          # FR-21: LLM-written Methods

    log_level: str = "INFO"
    max_retries: int = 3


settings = Settings()