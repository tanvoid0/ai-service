"""
Health check API routes
"""
from flask import Blueprint, jsonify
from app.models.responses import HealthResponse, DetailedHealthResponse
from app.services.ai_service import ai_service

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """
    Basic health check endpoint (no authentication required)
    
    Returns:
        {
            "status": "healthy",
            "service": "ai-service"
        }
    """
    response = HealthResponse(
        status="healthy",
        service="ai-service"
    )
    return jsonify(response.dict()), 200


@health_bp.route("/health", methods=["GET"], endpoint="detailed_health")
def detailed_health():
    """
    Detailed health check endpoint (no authentication required)
    
    Returns:
        {
            "status": "healthy",
            "service": "ai-service",
            "providers": {
                "ollama": {
                    "available": true,
                    "models_count": 5
                },
                "gemini": {
                    "available": true,
                    "models_count": 6
                }
            }
        }
    """
    providers_status = {}
    
    # Check each provider
    for provider_name in ai_service.get_available_providers():
        try:
            provider = ai_service.get_provider(provider_name)
            models = provider.get_available_models()
            
            providers_status[provider_name] = {
                "available": True,
                "models_count": len(models),
                "default_model": provider.get_default_model()
            }
        except Exception as e:
            providers_status[provider_name] = {
                "available": False,
                "error": str(e)
            }
    
    # Determine overall status
    all_healthy = all(
        status.get("available", False) 
        for status in providers_status.values()
    )
    overall_status = "healthy" if all_healthy else "degraded"
    
    response = DetailedHealthResponse(
        status=overall_status,
        service="ai-service",
        providers=providers_status
    )
    
    return jsonify(response.dict()), 200

