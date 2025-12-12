"""Configuration settings for the token-optimized BI system."""

from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    """Application settings."""
    
    # Database (read-only access to existing DB)
    database_url: str = "sqlite+aiosqlite:///../backend/data/cox_automotive.db"
    
    # Directory configurations
    dumps_dir: str = "./sql_dumps"
    cache_dir: str = "./cache"
    logs_dir: str = "./logs"
    
    # Pattern matching thresholds
    keyword_match_threshold: float = 0.6
    fuzzy_match_threshold: float = 0.4
    
    # Performance settings
    max_response_time_ms: int = 200
    max_concurrent_requests: int = 100
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/token_optimizer.log"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

# Global settings instance
settings = Settings()

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        settings.dumps_dir,
        settings.cache_dir,
        settings.logs_dir,
        f"{settings.dumps_dir}/sales_analytics",
        f"{settings.dumps_dir}/kpi_monitoring", 
        f"{settings.dumps_dir}/inventory_management",
        f"{settings.dumps_dir}/warranty_analysis",
        f"{settings.dumps_dir}/executive_reports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
if __name__ == "__main__":
    ensure_directories()
    print("✓ Directory structure created")