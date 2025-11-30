"""
Models API routes
"""
from flask import Blueprint, request, jsonify
from app.api.middleware import require_auth
from app.services.ai_service import ai_service
from app.models.responses import ProviderModelsResponse, AllModelsResponse
from app.config import config

models_bp = Blueprint("models", __name__)


@models_bp.route("/models", methods=["GET"])
@require_auth
def get_models():
    """
    Get available models
    
    Query params:
        provider: Filter by provider (ollama or gemini) - optional
        refresh: Force refresh of cached models (true/false) - optional
    
    Returns:
        If provider specified:
        {
            "provider": "ollama",
            "models": ["llama3.2:1b", "mistral:7b"],
            "default": "llama3.2:1b"
        }
        
        If no provider specified:
        {
            "providers": [
                {
                    "provider": "ollama",
                    "models": ["llama3.2:1b"],
                    "default": "llama3.2:1b"
                },
                {
                    "provider": "gemini",
                    "models": ["gemini-2.0-flash", "gemini-pro"],
                    "default": "gemini-2.0-flash"
                }
            ]
        }
    """
    try:
        provider_filter = request.args.get("provider")
        force_refresh = request.args.get("refresh", "false").lower() == "true"
        
        # If provider is specified, return only that provider's models
        if provider_filter:
            provider_filter = provider_filter.lower()
            
            if not ai_service.is_provider_available(provider_filter):
                return jsonify({
                    "error": "Provider not found",
                    "message": f"Provider '{provider_filter}' is not available"
                }), 404
            
            provider = ai_service.get_provider(provider_filter)
            # Use force_refresh if supported (both Ollama and Gemini support it)
            try:
                models = provider.get_available_models(force_refresh=force_refresh)
            except TypeError:
                # Fallback for providers that don't support force_refresh parameter
                models = provider.get_available_models()
            default = provider.get_default_model()
            
            response = ProviderModelsResponse(
                provider=provider_filter,
                models=models,
                default=default
            )
            
            return jsonify(response.dict()), 200
        
        # Otherwise, return all providers
        providers_data = []
        available_providers = ai_service.get_available_providers()
        
        # Log which providers are available
        print(f"[Models API] Available providers: {available_providers}")
        
        for provider_name in available_providers:
            try:
                provider = ai_service.get_provider(provider_name)
                # Use force_refresh if supported (both Ollama and Gemini support it)
                try:
                    models = provider.get_available_models(force_refresh=force_refresh)
                except TypeError:
                    # Fallback for providers that don't support force_refresh parameter
                    models = provider.get_available_models()
                default = provider.get_default_model()
                
                providers_data.append(ProviderModelsResponse(
                    provider=provider_name,
                    models=models,
                    default=default
                ))
            except Exception as e:
                # Log error but don't skip - include error info in response
                import traceback
                error_msg = f"Failed to get models for {provider_name}: {str(e)}"
                print(f"Warning: {error_msg}")
                print(traceback.format_exc())
                # Still include the provider but with empty models list
                providers_data.append(ProviderModelsResponse(
                    provider=provider_name,
                    models=[],
                    default=None
                ))
        
        response = AllModelsResponse(providers=providers_data)
        return jsonify(response.dict()), 200
    
    except Exception as e:
        return jsonify({
            "error": "Failed to get models",
            "message": str(e)
        }), 500


# Anonymous endpoint (no authentication required)
# Only available when ENABLE_ANONYMOUS_ACCESS=true

@models_bp.route("/models/anonymous", methods=["GET"])
def get_models_anonymous():
    """
    Anonymous models endpoint (no authentication required)
    Only available when ENABLE_ANONYMOUS_ACCESS=true
    
    Same request/response format as /models endpoint
    """
    if not config.ENABLE_ANONYMOUS_ACCESS:
        return jsonify({
            "error": "Anonymous access disabled",
            "message": "This endpoint is not available. Use /api/v1/models with authentication."
        }), 403
    
    # Use the same logic as the authenticated endpoint
    try:
        provider_filter = request.args.get("provider")
        force_refresh = request.args.get("refresh", "false").lower() == "true"
        
        if provider_filter:
            provider_filter = provider_filter.lower()
            
            if not ai_service.is_provider_available(provider_filter):
                return jsonify({
                    "error": "Provider not found",
                    "message": f"Provider '{provider_filter}' is not available"
                }), 404
            
            provider = ai_service.get_provider(provider_filter)
            try:
                models = provider.get_available_models(force_refresh=force_refresh)
            except TypeError:
                models = provider.get_available_models()
            default = provider.get_default_model()
            
            response = ProviderModelsResponse(
                provider=provider_filter,
                models=models,
                default=default
            )
            
            return jsonify(response.dict()), 200
        
        providers_data = []
        available_providers = ai_service.get_available_providers()
        
        for provider_name in available_providers:
            try:
                provider = ai_service.get_provider(provider_name)
                try:
                    models = provider.get_available_models(force_refresh=force_refresh)
                except TypeError:
                    models = provider.get_available_models()
                default = provider.get_default_model()
                
                providers_data.append(ProviderModelsResponse(
                    provider=provider_name,
                    models=models,
                    default=default
                ))
            except Exception as e:
                import traceback
                error_msg = f"Failed to get models for {provider_name}: {str(e)}"
                print(f"Warning: {error_msg}")
                print(traceback.format_exc())
                providers_data.append(ProviderModelsResponse(
                    provider=provider_name,
                    models=[],
                    default=None
                ))
        
        response = AllModelsResponse(providers=providers_data)
        return jsonify(response.dict()), 200
    
    except Exception as e:
        return jsonify({
            "error": "Failed to get models",
            "message": str(e)
        }), 500

