"""
Abstract base class for AI providers
"""
from abc import ABC, abstractmethod
from typing import List, Generator, Optional, Dict, Any


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, name: str):
        """
        Initialize the provider
        
        Args:
            name: Provider name (e.g., 'ollama', 'gemini')
        """
        self.name = name
    
    def generate_response(
        self, 
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generate a non-streaming response from the AI
        
        Args:
            prompt: The prompt/question to send (legacy, for backward compatibility)
            messages: Conversation history as list of dicts with 'role' and 'content'
            model: Optional specific model to use
        
        Returns:
            The generated response text
        
        Raises:
            Exception: If generation fails
        """
        # Convert prompt to messages if needed
        if messages is None:
            if prompt is None:
                raise ValueError("Either 'prompt' or 'messages' must be provided")
            messages = [{"role": "user", "content": prompt}]
        return self.generate_response_with_messages(messages, model)
    
    @abstractmethod
    def generate_response_with_messages(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> str:
        """
        Generate a non-streaming response from the AI using conversation history
        
        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'
            model: Optional specific model to use
        
        Returns:
            The generated response text
        
        Raises:
            Exception: If generation fails
        """
        pass
    
    def stream_response(
        self, 
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from the AI
        
        Args:
            prompt: The prompt/question to send (legacy, for backward compatibility)
            messages: Conversation history as list of dicts with 'role' and 'content'
            model: Optional specific model to use
        
        Yields:
            Chunks of the generated response text
        
        Raises:
            Exception: If streaming fails
        """
        # Convert prompt to messages if needed
        if messages is None:
            if prompt is None:
                raise ValueError("Either 'prompt' or 'messages' must be provided")
            messages = [{"role": "user", "content": prompt}]
        yield from self.stream_response_with_messages(messages, model)
    
    @abstractmethod
    def stream_response_with_messages(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from the AI using conversation history
        
        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'
            model: Optional specific model to use
        
        Yields:
            Chunks of the generated response text
        
        Raises:
            Exception: If streaming fails
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider
        
        Returns:
            List of model names/identifiers
        """
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """
        Get the default model for this provider
        
        Returns:
            Default model name/identifier
        """
        pass
    
    def validate_model(self, model: str) -> bool:
        """
        Validate if a model is available for this provider
        
        Args:
            model: Model name to validate
        
        Returns:
            True if model is available, False otherwise
        """
        available_models = self.get_available_models()
        return model in available_models if available_models else False

