"""
Security service client for token validation
"""
import requests
import logging
from typing import Dict, Optional
from app.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityServiceError(Exception):
    """Exception raised when security service validation fails"""
    pass


class SecurityClient:
    """Client for interacting with security-service"""
    
    def __init__(self, base_url: Optional[str] = None, application_id: Optional[str] = None):
        self.base_url = base_url or config.SECURITY_SERVICE_URL
        self.application_id = application_id or config.SECURITY_APPLICATION_ID
        self.validate_endpoint = f"{self.base_url}/api/v1/validate"
        self.check_endpoint = f"{self.base_url}/api/v1/validate/check"
        self.api_key_validate_endpoint = f"{self.base_url}/api/v1/apikeys/validate"
    
    def is_security_service_enabled(self) -> bool:
        """Check if security service is enabled"""
        return config.ENABLE_SECURITY_SERVICE
    
    def validate_hardcoded_api_key(self, api_key: str) -> Dict:
        """
        Validate API key against hardcoded key from config
        
        Args:
            api_key: API key string to validate
        
        Returns:
            Dictionary containing validation response with key info
        
        Raises:
            SecurityServiceError: If validation fails
        """
        if not config.HARDCODED_API_KEY:
            raise SecurityServiceError("Hardcoded API key not configured")
        
        if api_key != config.HARDCODED_API_KEY:
            raise SecurityServiceError("Invalid API key")
        
        # Return a response similar to security service format
        return {
            "keyId": "hardcoded-key",
            "valid": True,
            "message": "API key validated successfully"
        }
    
    def validate_token(
        self, 
        token: str, 
        path: str = "/", 
        method: str = "GET"
    ) -> Dict:
        """
        Validate a token with the security service
        
        Args:
            token: JWT token or session ID
            path: Resource path being accessed
            method: HTTP method (GET, POST, etc.)
        
        Returns:
            Dictionary containing validation response with user info
        
        Raises:
            SecurityServiceError: If validation fails
        """
        # If security service is disabled, tokens are not supported in standalone mode
        if not self.is_security_service_enabled():
            raise SecurityServiceError(
                "Token validation requires security service. "
                "Use API key authentication (X-API-Key header) for standalone mode."
            )
        
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Prepare validation request (use snake_case to match ValidationRequest record)
        validation_request = {
            "token": token,
            "application_id": self.application_id,
            "path": path,
            "http_method": method
        }
        
        try:
            logger.debug(f"Validating token with security service: {self.validate_endpoint}")
            logger.debug(f"Request: applicationId={self.application_id}, path={path}, method={method}")
            
            response = requests.post(
                self.validate_endpoint,
                json=validation_request,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            logger.debug(f"Security service response: status={response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("message", "Token is invalid or expired")
                logger.warning(f"Token validation failed (401): {error_msg}")
                raise SecurityServiceError(error_msg)
            elif response.status_code == 403:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("message", "Access denied")
                logger.warning(f"Access denied (403): {error_msg}")
                raise SecurityServiceError(error_msg)
            else:
                error_msg = f"Security service error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    error_msg = f"Security service error: {response.status_code} - {response.text[:200]}"
                logger.error(f"Unexpected security service response: {error_msg}")
                raise SecurityServiceError(error_msg)
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout connecting to security service at {self.validate_endpoint}")
            logger.error(f"Base URL: {self.base_url}, Application ID: {self.application_id}")
            # If hardcoded key is available, allow fallback
            if config.HARDCODED_API_KEY:
                logger.warning("Security service timeout, but hardcoded API key is available for fallback")
            raise SecurityServiceError(f"Timeout connecting to security service: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to security service at {self.validate_endpoint}")
            logger.error(f"Base URL: {self.base_url}, Application ID: {self.application_id}")
            logger.error(f"Error details: {str(e)}")
            # If hardcoded key is available, allow fallback
            if config.HARDCODED_API_KEY:
                logger.warning("Security service connection failed, but hardcoded API key is available for fallback")
            raise SecurityServiceError(f"Failed to connect to security service: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception to security service at {self.validate_endpoint}: {str(e)}")
            logger.error(f"Base URL: {self.base_url}, Application ID: {self.application_id}")
            # If hardcoded key is available, allow fallback
            if config.HARDCODED_API_KEY:
                logger.warning("Security service request failed, but hardcoded API key is available for fallback")
            raise SecurityServiceError(f"Failed to connect to security service: {str(e)}")
    
    def quick_check(self, token: str) -> Dict:
        """
        Quick token validation check (simplified)
        
        Args:
            token: JWT token or session ID
        
        Returns:
            Dictionary containing validation response
        
        Raises:
            SecurityServiceError: If validation fails
        """
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        try:
            response = requests.get(
                self.check_endpoint,
                params={
                    "token": token,
                    "application_id": self.application_id
                },
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise SecurityServiceError("Token is invalid or expired")
            elif response.status_code == 403:
                raise SecurityServiceError("Access denied")
            else:
                error_msg = f"Security service error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    pass
                raise SecurityServiceError(error_msg)
        
        except requests.exceptions.RequestException as e:
            raise SecurityServiceError(f"Failed to connect to security service: {str(e)}")
    
    def validate_api_key(
        self,
        api_key: str,
        resource_path: Optional[str] = None,
        http_method: Optional[str] = None
    ) -> Dict:
        """
        Validate an API key with the security service or hardcoded key
        
        Args:
            api_key: API key string (e.g., sk_live_... or hardcoded key)
            resource_path: Optional resource path being accessed
            http_method: Optional HTTP method (GET, POST, etc.)
        
        Returns:
            Dictionary containing validation response with key info
        
        Raises:
            SecurityServiceError: If validation fails
        """
        # If security service is disabled, use hardcoded key validation
        if not self.is_security_service_enabled():
            logger.debug("Security service disabled, validating against hardcoded API key")
            return self.validate_hardcoded_api_key(api_key)
        
        # Try security service first
        try:
            # Prepare validation request
            validation_request = {
                "api_key": api_key,
                "microservice": "ai-service",  # This microservice name
                "resource_path": resource_path,
                "http_method": http_method
            }
            
            logger.debug(f"Validating API key with security service: {self.api_key_validate_endpoint}")
            
            response = requests.post(
                self.api_key_validate_endpoint,
                json=validation_request,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            logger.debug(f"API key validation response: status={response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("message", "API key is invalid or does not have access")
                logger.warning(f"API key validation failed (403): {error_msg}")
                raise SecurityServiceError(error_msg)
            else:
                error_msg = f"Security service error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    error_msg = f"Security service error: {response.status_code} - {response.text[:200]}"
                logger.error(f"Unexpected security service response: {error_msg}")
                raise SecurityServiceError(error_msg)
        
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            # If security service fails but hardcoded key is available, fall back
            if config.HARDCODED_API_KEY:
                logger.warning(f"Security service unavailable ({str(e)}), falling back to hardcoded API key")
                try:
                    return self.validate_hardcoded_api_key(api_key)
                except SecurityServiceError:
                    # If hardcoded key also fails, raise original error
                    pass
            
            # Log and raise original error
            if isinstance(e, requests.exceptions.Timeout):
                logger.error(f"Timeout connecting to security service at {self.api_key_validate_endpoint}")
                raise SecurityServiceError(f"Timeout connecting to security service: {str(e)}")
            elif isinstance(e, requests.exceptions.ConnectionError):
                logger.error(f"Connection error to security service at {self.api_key_validate_endpoint}")
                raise SecurityServiceError(f"Failed to connect to security service: {str(e)}")
            else:
                logger.error(f"Request exception to security service at {self.api_key_validate_endpoint}: {str(e)}")
                raise SecurityServiceError(f"Failed to connect to security service: {str(e)}")
    
    def is_api_key(self, token: str) -> bool:
        """
        Check if a token is an API key (starts with sk_live_ or sk_test_)
        
        Args:
            token: Token string to check
        
        Returns:
            True if token appears to be an API key
        """
        if not token:
            return False
        # Remove Bearer prefix if present
        clean_token = token.replace("Bearer ", "").strip()
        return clean_token.startswith("sk_live_") or clean_token.startswith("sk_test_")


# Global instance
security_client = SecurityClient()

