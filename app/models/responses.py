"""
Response models for API endpoints
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="The AI-generated response")
    model: str = Field(..., description="The model used for generation")
    provider: str = Field(..., description="The provider used (ollama or gemini)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ModelInfo(BaseModel):
    """Information about a single model"""
    name: str = Field(..., description="Model name/identifier")
    provider: str = Field(..., description="Provider that supports this model")


class ProviderModelsResponse(BaseModel):
    """Response model for provider-specific models"""
    provider: str = Field(..., description="The provider name")
    models: List[str] = Field(..., description="List of available model names")
    default: str = Field(..., description="Default model for this provider")


class AllModelsResponse(BaseModel):
    """Response model for all models endpoint"""
    providers: List[ProviderModelsResponse] = Field(..., description="Models grouped by provider")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status (healthy, unhealthy)")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response"""
    providers: Dict[str, Dict[str, Any]] = Field(
        ..., 
        description="Status of each AI provider"
    )

