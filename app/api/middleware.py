"""
Authentication middleware for API routes
"""
from functools import wraps
from flask import request, jsonify
from app.services.security_client import security_client, SecurityServiceError
from app.config import config
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """
    Decorator to require authentication for a route
    
    Usage:
        @require_auth
        def my_route():
            user_id = request.user_id
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key first (X-API-Key header or Authorization header with API key)
        api_key = request.headers.get("X-API-Key")
        auth_header = request.headers.get("Authorization")
        
        # If no X-API-Key, check if Authorization header contains an API key
        if not api_key and auth_header:
            # Remove Bearer prefix if present
            token = auth_header.replace("Bearer ", "").strip()
            # Check if it's an API key format or if security service is disabled (treat as API key)
            if not config.ENABLE_SECURITY_SERVICE or security_client.is_api_key(token):
                api_key = token
        
        # If API key found, validate it
        if api_key:
            try:
                logger.debug(f"Validating API key for path: {request.path}, method: {request.method}")
                validation_result = security_client.validate_api_key(
                    api_key=api_key,
                    resource_path=request.path,
                    http_method=request.method
                )
                
                # Extract key ID from validation result
                key_id = validation_result.get("keyId")
                logger.debug(f"API key validated successfully: {key_id}")
                
                # Store key info in request context
                request.user_id = key_id  # Use keyId as user_id equivalent
                request.user_info = validation_result
                request.auth_type = "api_key"
                
                return f(*args, **kwargs)
            
            except SecurityServiceError as e:
                logger.error(f"API key validation failed: {str(e)}")
                return jsonify({
                    "error": "Authentication failed",
                    "message": str(e)
                }), 401
            
            except Exception as e:
                logger.error(f"Unexpected API key validation error: {str(e)}", exc_info=True)
                return jsonify({
                    "error": "Authentication error",
                    "message": f"Unexpected error: {str(e)}"
                }), 500
        
        # Fall back to JWT/session token validation (only if security service is enabled)
        if not config.ENABLE_SECURITY_SERVICE:
            return jsonify({
                "error": "Authentication required",
                "message": "Missing X-API-Key header or Authorization header with API key"
            }), 401
        
        if not auth_header:
            return jsonify({
                "error": "Authentication required",
                "message": "Missing Authorization header or X-API-Key header"
            }), 401
        
        # Extract token (keep Bearer prefix, security_client will handle it)
        token = auth_header
        
        # Validate token with security service
        try:
            logger.debug(f"Validating token for path: {request.path}, method: {request.method}")
            # Use the current request path and method for validation
            validation_result = security_client.validate_token(
                token=token,
                path=request.path,
                method=request.method
            )
            
            # Extract user ID from validation result
            user_id = validation_result.get("userId")
            logger.debug(f"Token validated successfully for user: {user_id}")
            
            # Store user info in request context
            request.user_id = user_id
            request.user_info = validation_result
            request.auth_type = "token"
            
            return f(*args, **kwargs)
        
        except SecurityServiceError as e:
            # Log the error for debugging
            logger.error(f"Security service validation failed: {str(e)}")
            logger.error(f"Path: {request.path}, Method: {request.method}")
            logger.error(f"Authorization header present: {bool(auth_header)}")
            return jsonify({
                "error": "Authentication failed",
                "message": str(e)
            }), 401
        
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected authentication error: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Authentication error",
                "message": f"Unexpected error: {str(e)}"
            }), 500
    
    return decorated_function


def optional_auth(f):
    """
    Decorator for optional authentication (doesn't fail if no token)
    
    Usage:
        @optional_auth
        def my_route():
            user_id = getattr(request, 'user_id', None)
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key first
        api_key = request.headers.get("X-API-Key")
        auth_header = request.headers.get("Authorization")
        
        # If no X-API-Key, check if Authorization header contains an API key
        if not api_key and auth_header:
            token = auth_header.replace("Bearer ", "").strip()
            # Check if it's an API key format or if security service is disabled (treat as API key)
            if not config.ENABLE_SECURITY_SERVICE or security_client.is_api_key(token):
                api_key = token
        
        # If API key found, validate it
        if api_key:
            try:
                validation_result = security_client.validate_api_key(
                    api_key=api_key,
                    resource_path=request.path,
                    http_method=request.method
                )
                key_id = validation_result.get("keyId")
                request.user_id = key_id
                request.user_info = validation_result
                request.auth_type = "api_key"
            except (SecurityServiceError, Exception):
                # Silently fail for optional auth
                pass
        # Fall back to JWT/session token validation (only if security service is enabled)
        elif auth_header and config.ENABLE_SECURITY_SERVICE:
            token = auth_header
            try:
                validation_result = security_client.validate_token(
                    token=token,
                    path=request.path,
                    method=request.method
                )
                user_id = validation_result.get("userId")
                request.user_id = user_id
                request.user_info = validation_result
                request.auth_type = "token"
            except (SecurityServiceError, Exception):
                # Silently fail for optional auth
                pass
        
        return f(*args, **kwargs)
    
    return decorated_function

