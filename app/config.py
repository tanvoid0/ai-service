"""
Configuration management for AI service
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""
    
    # Security Service Configuration
    ENABLE_SECURITY_SERVICE: bool = os.getenv(
        "ENABLE_SECURITY_SERVICE",
        "true"
    ).lower() in ("true", "1", "yes", "on")
    
    SECURITY_SERVICE_URL: str = os.getenv(
        "SECURITY_SERVICE_URL", 
        "http://localhost:8080"
    )
    FRONTEND_SECURITY_SERVICE_URL: Optional[str] = os.getenv("FRONTEND_SECURITY_SERVICE_URL")
    SECURITY_APPLICATION_ID: str = os.getenv(
        "SECURITY_APPLICATION_ID",
        "ai-service"
    )
    
    # Hardcoded API Key (for standalone mode without security service)
    HARDCODED_API_KEY: Optional[str] = os.getenv("HARDCODED_API_KEY")
    
    # Anonymous Access (for testing/development)
    # When enabled, anonymous endpoints are available without authentication
    ENABLE_ANONYMOUS_ACCESS: bool = os.getenv(
        "ENABLE_ANONYMOUS_ACCESS",
        "false"
    ).lower() in ("true", "1", "yes", "on")
    
    # Database Configuration
    # For standalone mode: use external database URL (e.g., MongoDB Atlas, hosted database)
    # For microservices mode: use db-service URL (e.g., mongodb://db-service:27017)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DATABASE_NAME: Optional[str] = os.getenv("DATABASE_NAME", "ai_service_db")
    
    # AI Provider Configuration
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    )
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Flask Configuration
    # Render.com uses PORT environment variable, fallback to FLASK_PORT
    FLASK_PORT: int = int(os.getenv("PORT") or os.getenv("FLASK_PORT", "8081"))
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    
    # Default Provider
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "ollama")
    
    # Validation
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not set. Gemini provider will not work.")
        
        if not cls.ENABLE_SECURITY_SERVICE:
            if not cls.HARDCODED_API_KEY:
                raise ValueError(
                    "HARDCODED_API_KEY must be set when ENABLE_SECURITY_SERVICE is false. "
                    "Set HARDCODED_API_KEY in your .env file for standalone mode."
                )
            print("Security service is disabled. Using hardcoded API key for authentication.")
        else:
            if not cls.SECURITY_APPLICATION_ID:
                raise ValueError("SECURITY_APPLICATION_ID must be set when security service is enabled")


# Create global config instance
config = Config()

