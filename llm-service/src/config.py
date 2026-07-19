"""LLM Service configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_port: int = 8500
    app_debug: bool = True

    llm_model: str = "llama3-70b"
    llm_endpoint: str = "http://localhost:8001/v1"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.1
    llm_context_window: int = 8192

    retrieval_top_k: int = 5
    embedding_model: str = "BAAI/bge-m3"


llm_config = LLMConfig()
