"""
Chat API routes
"""
from flask import Blueprint, request, jsonify, Response, stream_with_context
from app.api.middleware import require_auth
from app.services.ai_service import ai_service
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.config import config
import json

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
@require_auth
def chat():
    """
    Non-streaming chat endpoint
    
    Request body (new format with conversation history):
        {
            "messages": [
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ],
            "model": "llama3.2:1b",  # optional
            "provider": "ollama",     # optional
            "max_context_messages": 20  # optional, default: 20
        }
    
    Request body (legacy format - still supported):
        {
            "prompt": "Hello, how are you?",
            "model": "llama3.2:1b",  # optional
            "provider": "ollama"      # optional
        }
    
    Returns:
        {
            "response": "I'm doing well, thank you!",
            "model": "llama3.2:1b",
            "provider": "ollama"
        }
    """
    try:
        # Parse and validate request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        chat_request = ChatRequest(**data)
        
        # Get provider
        provider = ai_service.get_provider(chat_request.provider)
        
        # Get messages (with context limiting applied)
        messages = chat_request.get_messages()
        
        # Generate response
        response_text = provider.generate_response(
            messages=messages,
            model=chat_request.model
        )
        
        # Get the model that was actually used
        used_model = chat_request.model or provider.get_default_model()
        
        # Build response
        chat_response = ChatResponse(
            response=response_text,
            model=used_model,
            provider=provider.name
        )
        
        return jsonify(chat_response.dict()), 200
    
    except ValueError as e:
        return jsonify({"error": "Invalid request", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Generation failed", "message": str(e)}), 500


@chat_bp.route("/chat/stream", methods=["POST"])
@require_auth
def chat_stream():
    """
    Streaming chat endpoint (Server-Sent Events)
    
    Request body (new format with conversation history):
        {
            "messages": [
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ],
            "model": "llama3.2:1b",  # optional
            "provider": "ollama",     # optional
            "max_context_messages": 20  # optional, default: 20
        }
    
    Request body (legacy format - still supported):
        {
            "prompt": "Hello, how are you?",
            "model": "llama3.2:1b",  # optional
            "provider": "ollama"      # optional
        }
    
    Returns:
        Server-Sent Events stream with chunks
    """
    try:
        # Parse and validate request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        chat_request = ChatRequest(**data)
        
        # Get provider
        provider = ai_service.get_provider(chat_request.provider)
        
        # Get the model that will be used
        used_model = chat_request.model or provider.get_default_model()
        
        # Get messages (with context limiting applied)
        messages = chat_request.get_messages()
        
        def generate():
            """Generator function for streaming response"""
            try:
                # Send initial metadata
                metadata = {
                    "type": "metadata",
                    "model": used_model,
                    "provider": provider.name
                }
                yield f"data: {json.dumps(metadata)}\n\n"
                
                # Stream response chunks
                for chunk in provider.stream_response(
                    messages=messages,
                    model=chat_request.model
                ):
                    chunk_data = {
                        "type": "chunk",
                        "content": chunk
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send completion signal
                completion = {
                    "type": "done"
                }
                yield f"data: {json.dumps(completion)}\n\n"
            
            except Exception as e:
                error_data = {
                    "type": "error",
                    "message": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering in nginx
            }
        )
    
    except ValueError as e:
        return jsonify({"error": "Invalid request", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Streaming failed", "message": str(e)}), 500


# Anonymous endpoints (no authentication required)
# Only available when ENABLE_ANONYMOUS_ACCESS=true

@chat_bp.route("/chat/anonymous", methods=["POST"])
def chat_anonymous():
    """
    Anonymous chat endpoint (no authentication required)
    Only available when ENABLE_ANONYMOUS_ACCESS=true
    
    Same request/response format as /chat endpoint
    """
    if not config.ENABLE_ANONYMOUS_ACCESS:
        return jsonify({
            "error": "Anonymous access disabled",
            "message": "This endpoint is not available. Use /api/v1/chat with authentication."
        }), 403
    
    # Use the same logic as the authenticated endpoint
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        chat_request = ChatRequest(**data)
        provider = ai_service.get_provider(chat_request.provider)
        messages = chat_request.get_messages()
        response_text = provider.generate_response(
            messages=messages,
            model=chat_request.model
        )
        used_model = chat_request.model or provider.get_default_model()
        
        chat_response = ChatResponse(
            response=response_text,
            model=used_model,
            provider=provider.name
        )
        
        return jsonify(chat_response.dict()), 200
    
    except ValueError as e:
        return jsonify({"error": "Invalid request", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Generation failed", "message": str(e)}), 500


@chat_bp.route("/chat/stream/anonymous", methods=["POST"])
def chat_stream_anonymous():
    """
    Anonymous streaming chat endpoint (no authentication required)
    Only available when ENABLE_ANONYMOUS_ACCESS=true
    
    Same request/response format as /chat/stream endpoint
    """
    if not config.ENABLE_ANONYMOUS_ACCESS:
        return jsonify({
            "error": "Anonymous access disabled",
            "message": "This endpoint is not available. Use /api/v1/chat/stream with authentication."
        }), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        chat_request = ChatRequest(**data)
        provider = ai_service.get_provider(chat_request.provider)
        used_model = chat_request.model or provider.get_default_model()
        messages = chat_request.get_messages()
        
        def generate():
            try:
                metadata = {
                    "type": "metadata",
                    "model": used_model,
                    "provider": provider.name
                }
                yield f"data: {json.dumps(metadata)}\n\n"
                
                for chunk in provider.stream_response(
                    messages=messages,
                    model=chat_request.model
                ):
                    chunk_data = {
                        "type": "chunk",
                        "content": chunk
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                completion = {"type": "done"}
                yield f"data: {json.dumps(completion)}\n\n"
            
            except Exception as e:
                error_data = {
                    "type": "error",
                    "message": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except ValueError as e:
        return jsonify({"error": "Invalid request", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Streaming failed", "message": str(e)}), 500

