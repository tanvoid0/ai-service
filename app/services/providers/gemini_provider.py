"""
Google Gemini AI provider implementation
"""
from typing import List, Optional, Generator, Dict
from app.services.providers.base import AIProvider
from app.config import config

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


class GeminiProvider(AIProvider):
    """Google Gemini provider implementation"""
    
    # Comprehensive list of Gemini models sorted by price (cheapest first)
    # Pricing reference: https://ai.google.dev/pricing
    # Order: Flash-Lite (cheapest) -> Flash -> Pro (most expensive)
    GEMINI_MODELS_BY_PRICE = [
        "gemini-2.0-flash-lite",      # Cheapest: $0.10/$0.40 per M tokens
        "gemini-2.0-flash-exp",       # Experimental flash
        "gemini-2.0-flash",           # Fast and efficient: ~$0.15/$0.50
        "gemini-1.5-flash",           # Previous generation flash
        "gemini-1.5-flash-8b",        # Smaller flash variant
        "gemini-1.5-pro",             # Pro model: ~$1.25/$5.00
        "gemini-1.5-pro-latest",      # Latest pro variant
        "gemini-pro",                 # Original pro
        "gemini-pro-vision"           # Vision-capable pro
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini provider
        
        Args:
            api_key: Google Gemini API key (defaults to config)
        """
        super().__init__("gemini")
        
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai package is not installed")
        
        self.api_key = api_key or config.GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.default_model = "gemini-2.0-flash"
        self._cached_models: Optional[List[str]] = None
        
        print(f"[GeminiProvider] Initialized with API key: {'***' + self.api_key[-4:] if len(self.api_key) > 4 else '***'}")
    
    def get_available_models(self, force_refresh: bool = False) -> List[str]:
        """
        Get available Gemini models, trying to fetch from API first,
        falling back to hardcoded list sorted by price
        
        Args:
            force_refresh: If True, clear cache and fetch fresh data
        
        Returns:
            List of available model names (sorted by price, cheapest first)
        """
        print(f"[GeminiProvider.get_available_models] Called with force_refresh={force_refresh}")
        
        # Clear cache if force refresh is requested
        if force_refresh:
            print(f"[GeminiProvider.get_available_models] Clearing cache due to force_refresh")
            self._cached_models = None
        
        # Return cached models if available
        if self._cached_models is not None:
            print(f"[GeminiProvider.get_available_models] Returning {len(self._cached_models)} cached models")
            return self._cached_models.copy()
        
        print(f"[GeminiProvider.get_available_models] Attempting to fetch models from Gemini API...")
        
        # Try to fetch models dynamically from API
        try:
            # The google-genai library may have a way to list models
            # If not available, we'll fall back to the hardcoded list
            models = self._fetch_models_from_api()
            if models:
                print(f"[GeminiProvider.get_available_models] Successfully fetched {len(models)} models from API")
                # Sort by price (using our price-ordered list as reference)
                models = self._sort_models_by_price(models)
                self._cached_models = models
                return models.copy()
        except Exception as e:
            print(f"[GeminiProvider.get_available_models] Failed to fetch from API: {str(e)}")
            print(f"[GeminiProvider.get_available_models] Falling back to hardcoded list")
        
        # Fallback to hardcoded list sorted by price
        print(f"[GeminiProvider.get_available_models] Using hardcoded list of {len(self.GEMINI_MODELS_BY_PRICE)} models")
        self._cached_models = self.GEMINI_MODELS_BY_PRICE.copy()
        return self._cached_models.copy()
    
    def _fetch_models_from_api(self) -> List[str]:
        """
        Attempt to fetch available models from Gemini API
        
        Returns:
            List of model names, or empty list if not available
        """
        try:
            # Try to list models using the client
            # Note: The exact API may vary, this is a best-effort attempt
            if hasattr(self.client, 'models') and hasattr(self.client.models, 'list'):
                print(f"[GeminiProvider._fetch_models_from_api] Attempting to list models via client.models.list()")
                models_list = self.client.models.list()
                models = []
                for model in models_list:
                    if hasattr(model, 'name'):
                        model_name = model.name
                        # Extract just the model identifier (e.g., "gemini-2.0-flash" from full path)
                        if '/' in model_name:
                            model_name = model_name.split('/')[-1]
                        models.append(model_name)
                        print(f"[GeminiProvider._fetch_models_from_api] Found model: {model_name}")
                return models
            else:
                print(f"[GeminiProvider._fetch_models_from_api] Client doesn't support model listing")
                return []
        except Exception as e:
            print(f"[GeminiProvider._fetch_models_from_api] Error fetching models: {str(e)}")
            return []
    
    def _sort_models_by_price(self, models: List[str]) -> List[str]:
        """
        Sort models by price using our price-ordered list as reference
        
        Args:
            models: List of model names to sort
        
        Returns:
            Sorted list (cheapest first)
        """
        # Create a mapping of model to price order (lower index = cheaper)
        price_order = {model: idx for idx, model in enumerate(self.GEMINI_MODELS_BY_PRICE)}
        
        def get_price_order(model_name: str) -> int:
            # Check for exact match first
            if model_name in price_order:
                return price_order[model_name]
            # Check for partial matches (e.g., "gemini-2.0-flash-latest" matches "gemini-2.0-flash")
            for ordered_model in self.GEMINI_MODELS_BY_PRICE:
                if ordered_model in model_name or model_name in ordered_model:
                    return price_order[ordered_model]
            # Unknown models go to the end
            return 9999
        
        sorted_models = sorted(models, key=get_price_order)
        print(f"[GeminiProvider._sort_models_by_price] Sorted {len(sorted_models)} models by price")
        return sorted_models
    
    def get_default_model(self) -> str:
        """
        Get default Gemini model
        
        Returns:
            Default model name
        """
        return self.default_model
    
    def generate_response_with_messages(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> str:
        """
        Generate a non-streaming response from Gemini using conversation history
        
        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'
            model: Optional specific model to use
        
        Returns:
            The generated response text
        
        Raises:
            Exception: If generation fails
        """
        selected_model = model or self.get_default_model()
        
        # Validate model - get current available models
        available_models = self.get_available_models()
        if selected_model not in available_models:
            raise ValueError(f"Model {selected_model} is not available. Available models: {available_models}")
        
        try:
            # Convert messages to Gemini format
            # Gemini expects contents as a list of parts with role
            contents = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # Gemini uses 'user' and 'model' roles (not 'assistant')
                if role == "assistant":
                    role = "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": content}]
                })
            
            response = self.client.models.generate_content(
                model=selected_model,
                contents=contents
            )
            
            return response.text if hasattr(response, 'text') else str(response)
        
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def stream_response_with_messages(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from Gemini using conversation history
        
        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'
            model: Optional specific model to use
        
        Yields:
            Chunks of the generated response text
        
        Raises:
            Exception: If streaming fails
        """
        selected_model = model or self.get_default_model()
        
        # Validate model - get current available models
        available_models = self.get_available_models()
        if selected_model not in available_models:
            raise ValueError(f"Model {selected_model} is not available. Available models: {available_models}")
        
        try:
            # Convert messages to Gemini format
            # Gemini expects contents as a list of parts with role
            contents = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # Gemini uses 'user' and 'model' roles (not 'assistant')
                if role == "assistant":
                    role = "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": content}]
                })
            
            stream_iter = self.client.models.generate_content_stream(
                model=selected_model,
                contents=contents
            )
            
            for chunk in stream_iter:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                elif isinstance(chunk, str):
                    yield chunk
        
        except Exception as e:
            raise Exception(f"Gemini API stream error: {str(e)}")

