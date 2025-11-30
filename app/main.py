"""
Flask application main entry point
"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from app.config import config
from app.api.routes.chat import chat_bp
from app.api.routes.models import models_bp
from app.api.routes.health import health_bp
import os


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(chat_bp, url_prefix="/api/v1")
    app.register_blueprint(models_bp, url_prefix="/api/v1")
    app.register_blueprint(health_bp)  # Basic health at /health
    
    # Register detailed health at /api/v1/health
    from app.api.routes.health import detailed_health
    app.add_url_rule("/api/v1/health", "detailed_health", detailed_health, methods=["GET"])
    
    # Serve React app static assets
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)
    
    # Serve React app - SPA routing: all non-API routes serve index.html
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react_app(path):
        # Don't serve index.html for API routes
        if path.startswith('api/'):
            return jsonify({"error": "Not found", "message": "The requested resource was not found"}), 404
        
        # Serve index.html for all other routes (SPA routing)
        return send_from_directory(app.static_folder, 'index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        # For API routes, return JSON error
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Not found",
                "message": "The requested resource was not found"
            }), 404
        # For non-API routes, serve React app (SPA routing)
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "Bad request",
            "message": "Invalid request data"
        }), 400
    
    # API info endpoint
    @app.route("/api")
    def api_info():
        return jsonify({
            "service": "ai-service",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "chat": "/api/v1/chat",
                "chat_stream": "/api/v1/chat/stream",
                "models": "/api/v1/models",
                "health": "/health"
            }
        })
    
    # Config endpoint for frontend
    @app.route("/api/config")
    def get_config():
        # Frontend runs in browser, needs public URL (localhost), not Docker internal URL
        # Use FRONTEND_SECURITY_SERVICE_URL if set, otherwise convert internal URL to public
        if config.FRONTEND_SECURITY_SERVICE_URL:
            security_url = config.FRONTEND_SECURITY_SERVICE_URL
        else:
            security_url = config.SECURITY_SERVICE_URL
            # Convert Docker/Kubernetes internal hostname to localhost for browser access
            if "security-service" in security_url:
                # Replace any occurrence of security-service with localhost
                security_url = security_url.replace("security-service", "localhost")
        
        return jsonify({
            "securityServiceUrl": security_url,
            "applicationId": config.SECURITY_APPLICATION_ID,
            "version": "2.2.0"
        })
    
    # Diagnostic endpoint to test security service connection
    @app.route("/api/debug/security")
    def debug_security():
        """Debug endpoint to test security service connectivity"""
        from app.services.security_client import security_client
        import requests
        import logging
        
        logger = logging.getLogger(__name__)
        
        debug_info = {
            "security_service_url": config.SECURITY_SERVICE_URL,
            "application_id": config.SECURITY_APPLICATION_ID,
            "connectivity": {},
            "validation_endpoint": security_client.validate_endpoint
        }
        
        # Test basic connectivity to health endpoint
        try:
            health_url = f"{config.SECURITY_SERVICE_URL}/q/health"
            logger.info(f"Testing connectivity to: {health_url}")
            health_response = requests.get(health_url, timeout=5)
            debug_info["connectivity"]["health_check"] = {
                "url": health_url,
                "status": health_response.status_code,
                "reachable": True,
                "response": health_response.text[:200] if health_response.text else None
            }
        except requests.exceptions.Timeout as e:
            debug_info["connectivity"]["health_check"] = {
                "url": health_url,
                "status": "timeout",
                "reachable": False,
                "error": f"Timeout: {str(e)}"
            }
        except requests.exceptions.ConnectionError as e:
            debug_info["connectivity"]["health_check"] = {
                "url": health_url,
                "status": "connection_error",
                "reachable": False,
                "error": f"Connection error: {str(e)}"
            }
        except Exception as e:
            debug_info["connectivity"]["health_check"] = {
                "url": health_url,
                "status": "error",
                "reachable": False,
                "error": str(e)
            }
        
        # Test validation endpoint
        try:
            validate_url = security_client.validate_endpoint
            logger.info(f"Testing validation endpoint: {validate_url}")
            # Try a dummy request to see if endpoint is reachable
            test_response = requests.post(
                validate_url,
                json={"token": "test", "applicationId": config.SECURITY_APPLICATION_ID, "path": "/", "httpMethod": "GET"},
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            debug_info["connectivity"]["validation_endpoint"] = {
                "url": validate_url,
                "status": test_response.status_code,
                "reachable": True,
                "note": "Endpoint is reachable (expected 401 for invalid token)"
            }
        except requests.exceptions.Timeout as e:
            debug_info["connectivity"]["validation_endpoint"] = {
                "url": validate_url,
                "status": "timeout",
                "reachable": False,
                "error": f"Timeout: {str(e)}"
            }
        except requests.exceptions.ConnectionError as e:
            debug_info["connectivity"]["validation_endpoint"] = {
                "url": validate_url,
                "status": "connection_error",
                "reachable": False,
                "error": f"Connection error: {str(e)}"
            }
        except Exception as e:
            debug_info["connectivity"]["validation_endpoint"] = {
                "url": validate_url,
                "status": "error",
                "reachable": False,
                "error": str(e)
            }
        
        return jsonify(debug_info)
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        exit(1)
    
    # Run the application
    app.run(
        host="0.0.0.0",
        port=config.FLASK_PORT,
        debug=(config.FLASK_ENV == "development")
    )

