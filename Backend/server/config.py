"""Configuration management for MedCompanion server."""

import os
from pathlib import Path
from typing import List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server settings
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_reload: bool = False  # Disabled to prevent MPS issues
    
    # Model settings
    model_name: str = "google/medgemma-4b-it"
    model_device: str = "auto"
    model_dtype: str = "float16"
    
    # MedASR settings
    medasr_model_name: str = "google/medasr"
    medasr_chunk_length_s: int = 30
    medasr_stride_length_s: int = 5
    
    # Database settings
    database_url: str = "sqlite:///./medcompanion.db"
    
    # Storage settings
    storage_path: Path = Path("./storage")
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Ensure storage directory exists
settings.storage_path.mkdir(parents=True, exist_ok=True)
