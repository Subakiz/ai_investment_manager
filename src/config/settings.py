"""
Configuration management for AlphaGen Investment Platform
"""
import os
from typing import Optional
from pathlib import Path

# Try to load dotenv, but don't fail if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

class Config:
    """Application configuration class"""
    
    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "alphagen")
    DB_USER: str = os.getenv("DB_USER", "alphauser")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "alphapass")
    
    @property
    def database_url(self) -> str:
        """Get complete database URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def async_database_url(self) -> str:
        """Get async database URL"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # API Keys
    NEWS_API_KEY: Optional[str] = os.getenv("NEWS_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Data Pipeline Configuration
    LQ45_UPDATE_TIME: str = os.getenv("LQ45_UPDATE_TIME", "09:30")  # UTC
    NEWS_UPDATE_TIME: str = os.getenv("NEWS_UPDATE_TIME", "09:45")  # UTC
    
    # Application Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    TZ: str = os.getenv("TZ", "Asia/Jakarta")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # External APIs
    IDX_API_BASE_URL: str = os.getenv("IDX_API_BASE_URL", "https://finance.yahoo.com")
    NEWS_KEYWORDS: str = os.getenv("NEWS_KEYWORDS", "IDX,Bursa Efek Indonesia,saham Indonesia,LQ45")
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    
    def __init__(self):
        """Initialize configuration and create necessary directories"""
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.DATA_DIR.mkdir(exist_ok=True)
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        required_settings = []
        
        if self.ENVIRONMENT == "production":
            required_settings.extend([
                ("NEWS_API_KEY", self.NEWS_API_KEY),
                ("GEMINI_API_KEY", self.GEMINI_API_KEY),
            ])
        
        missing_settings = [name for name, value in required_settings if not value]
        
        if missing_settings:
            raise ValueError(f"Missing required configuration: {', '.join(missing_settings)}")
        
        return True

# Global configuration instance
config = Config()