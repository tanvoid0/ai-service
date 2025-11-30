"""
AI Service - Factory and orchestration for AI providers
"""
from typing import Optional, Dict
from app.services.providers.base import AIProvider
from app.services.providers.ollama_provider import OllamaProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.config import config


class AIService:
    """Main AI service for managing providers"""
    
    def __init__(self):
        """Initialize AI service with provider instances"""
        self._providers: Dict[str, AIProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers"""
        import traceback
        
        # Initialize Ollama provider
        try:
            self._providers["ollama"] = OllamaProvider()
            print("[AIService] Ollama provider initialized successfully")
        except Exception as e:
            print(f"[AIService] Warning: Failed to initialize Ollama provider: {e}")
            print(traceback.format_exc())
        
        # Initialize Gemini provider
        try:
            self._providers["gemini"] = GeminiProvider()
            print("[AIService] Gemini provider initialized successfully")
        except Exception as e:
            print(f"[AIService] Error: Failed to initialize Gemini provider: {e}")
            print(f"[AIService] Error type: {type(e).__name__}")
            print(traceback.format_exc())
            # Check if it's an API key issue
            from app.config import config
            if not config.GEMINI_API_KEY:
                print("[AIService] GEMINI_API_KEY is not set in environment")
            else:
                print(f"[AIService] GEMINI_API_KEY is set (length: {len(config.GEMINI_API_KEY)})")
    
    def get_provider(self, provider_type: Optional[str] = None) -> AIProvider:
        """
        Get an AI provider instance
        
        Args:
            provider_type: Provider type ('ollama' or 'gemini'). 
                         If None, uses default from config.
        
        Returns:
            AIProvider instance
        
        Raises:
            ValueError: If provider is not available or not found
        """
        if provider_type is None:
            provider_type = config.DEFAULT_PROVIDER
        
        provider_type = provider_type.lower()
        
        if provider_type not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(
                f"Provider '{provider_type}' is not available. "
                f"Available providers: {available}"
            )
        
        return self._providers[provider_type]
    
    def get_available_providers(self) -> list[str]:
        """
        Get list of available provider names
        
        Returns:
            List of provider names
        """
        return list(self._providers.keys())
    
    def is_provider_available(self, provider_type: str) -> bool:
        """
        Check if a provider is available
        
        Args:
            provider_type: Provider type to check
        
        Returns:
            True if provider is available, False otherwise
        """
        return provider_type.lower() in self._providers


# Global instance
ai_service = AIService()

