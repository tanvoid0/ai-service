"""
Request models for API endpoints
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Message model for conversation history"""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., min_length=1, description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    # Support both old format (prompt) and new format (messages)
    prompt: Optional[str] = Field(None, description="Single prompt (legacy format, for backward compatibility)")
    messages: Optional[List[ChatMessage]] = Field(None, description="Conversation history as messages array")
    model: Optional[str] = Field(None, description="Specific model to use (optional)")
    provider: Optional[str] = Field(None, description="AI provider to use (ollama or gemini)")
    max_context_messages: Optional[int] = Field(None, ge=1, le=100, description="Maximum number of previous messages to include (default: 20)")
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get messages in format expected by providers.
        Converts prompt to messages if only prompt is provided.
        Applies context window limiting.
        """
        if self.messages:
            # Limit context if specified
            max_messages = self.max_context_messages or 20
            limited_messages = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
            return [{"role": msg.role, "content": msg.content} for msg in limited_messages]
        elif self.prompt:
            # Legacy format: convert single prompt to messages
            return [{"role": "user", "content": self.prompt}]
        else:
            raise ValueError("Either 'prompt' or 'messages' must be provided")
    
    @classmethod
    def model_validate(cls, obj: Any) -> 'ChatRequest':
        """Custom validation to ensure either prompt or messages is provided"""
        instance = super().model_validate(obj)
        if not instance.prompt and not instance.messages:
            raise ValueError("Either 'prompt' or 'messages' must be provided")
        return instance


class ModelsRequest(BaseModel):
    """Request model for models endpoint (query params)"""
    provider: Optional[str] = Field(None, description="Filter by provider (ollama or gemini)")

