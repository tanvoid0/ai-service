"""
Ollama AI provider implementation
"""
import requests
import json
import re
from typing import List, Optional, Generator, Dict
from app.services.providers.base import AIProvider
from app.config import config


class OllamaProvider(AIProvider):
    """Ollama provider implementation"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama provider
        
        Args:
            base_url: Ollama server base URL (defaults to config)
        """
        super().__init__("ollama")
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.chat_endpoint = f"{self.base_url}/api/chat"
        self.tags_endpoint = f"{self.base_url}/api/tags"
        self._cached_models: Optional[List[str]] = None
        self._model_metadata: Dict[str, Dict] = {}  # Store model metadata (size, etc.)
        
        print(f"[OllamaProvider] Initialized with base_url: {self.base_url}")
        print(f"[OllamaProvider] Tags endpoint: {self.tags_endpoint}")
        print(f"[OllamaProvider] Generate endpoint: {self.generate_endpoint}")
        print(f"[OllamaProvider] Chat endpoint: {self.chat_endpoint}")
    
    def clear_cache(self):
        """Clear the cached models to force a fresh fetch"""
        self._cached_models = None
        self._model_metadata = {}
    
    def _estimate_model_size(self, model_name: str) -> int:
        """
        Estimate model size from name to help prioritize smaller models.
        Returns estimated parameter count in billions (e.g., 1 for 1b, 7 for 7b, 70 for 70b).
        Lower number = smaller model = preferred for default.
        """
        model_lower = model_name.lower()
        
        # Extract size indicators from model name
        # Patterns: llama3.2:1b, qwen2.5:14b, llama3.1:70b, etc.
        
        # Look for patterns like :1b, :7b, :14b, :32b, :70b
        size_match = re.search(r':(\d+)b', model_lower)
        if size_match:
            return int(size_match.group(1))
        
        # Look for patterns like -1b, -7b, etc.
        size_match = re.search(r'-(\d+)b', model_lower)
        if size_match:
            return int(size_match.group(1))
        
        # Look for patterns like 1b, 7b, 14b in the name
        size_match = re.search(r'(\d+)b', model_lower)
        if size_match:
            return int(size_match.group(1))
        
        # Default: assume larger models if no size found (prioritize known small models)
        if any(x in model_lower for x in ['1b', '1.5b', '2b', '3b']):
            return 1
        elif any(x in model_lower for x in ['7b', '8b']):
            return 7
        elif any(x in model_lower for x in ['13b', '14b']):
            return 14
        elif any(x in model_lower for x in ['32b', '34b']):
            return 32
        elif any(x in model_lower for x in ['70b', '72b']):
            return 70
        
        # Unknown size - assume medium (will be sorted after known small models)
        return 50
    
    def get_available_models(self, force_refresh: bool = False) -> List[str]:
        """
        Get available models from Ollama API
        
        Args:
            force_refresh: If True, clear cache and fetch fresh data
        
        Returns:
            List of available model names (sorted by name)
        """
        print(f"[OllamaProvider.get_available_models] Called with force_refresh={force_refresh}")
        print(f"[OllamaProvider.get_available_models] Cache status: {self._cached_models is not None}")
        
        # Clear cache if force refresh is requested
        if force_refresh:
            print(f"[OllamaProvider.get_available_models] Clearing cache due to force_refresh")
            self.clear_cache()
        
        # Return cached models if available
        if self._cached_models is not None:
            print(f"[OllamaProvider.get_available_models] Returning {len(self._cached_models)} cached models")
            return sorted(self._cached_models)  # Sort by name
        
        print(f"[OllamaProvider.get_available_models] No cache, fetching from API...")
        print(f"[OllamaProvider.get_available_models] Making GET request to: {self.tags_endpoint}")
        
        try:
            import time
            start_time = time.time()
            response = requests.get(self.tags_endpoint, timeout=10)
            elapsed = time.time() - start_time
            
            print(f"[OllamaProvider.get_available_models] Request completed in {elapsed:.2f}s")
            print(f"[OllamaProvider.get_available_models] Response status: {response.status_code}")
            print(f"[OllamaProvider.get_available_models] Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[OllamaProvider.get_available_models] Response JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    print(f"[OllamaProvider.get_available_models] Full response data:\n{json.dumps(data, indent=2)}")
                    
                    models = []
                    
                    if "models" in data:
                        if isinstance(data["models"], list):
                            print(f"[OllamaProvider.get_available_models] Found 'models' key with {len(data['models'])} items")
                            for idx, model_info in enumerate(data["models"]):
                                print(f"[OllamaProvider.get_available_models] Processing model {idx + 1}: {model_info}")
                                # Ollama returns model info with 'name' or 'model' field
                                model_name = model_info.get("name") or model_info.get("model")
                                if model_name:
                                    models.append(model_name)
                                    # Store model metadata (size, etc.)
                                    size = model_info.get("size", 0)
                                    self._model_metadata[model_name] = {
                                        "size": size,
                                        "estimated_params": self._estimate_model_size(model_name)
                                    }
                                    print(f"[OllamaProvider.get_available_models] ✓ Added model: {model_name} (estimated: {self._estimate_model_size(model_name)}B params)")
                                else:
                                    print(f"[OllamaProvider.get_available_models] ✗ Warning: Model info missing name/model field. Full info: {json.dumps(model_info, indent=2)}")
                        else:
                            print(f"[OllamaProvider.get_available_models] ✗ Warning: 'models' key exists but is not a list. Type: {type(data['models'])}, Value: {data['models']}")
                    else:
                        print(f"[OllamaProvider.get_available_models] ✗ Warning: Response missing 'models' key")
                        print(f"[OllamaProvider.get_available_models] Available keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    # Sort models by name
                    models = sorted(models)
                    print(f"[OllamaProvider.get_available_models] Total models found and sorted: {len(models)}")
                    print(f"[OllamaProvider.get_available_models] Models list: {models}")
                    
                    self._cached_models = models
                    return models
                except json.JSONDecodeError as json_err:
                    print(f"[OllamaProvider.get_available_models] ✗ JSON decode error: {str(json_err)}")
                    print(f"[OllamaProvider.get_available_models] Response text (first 1000 chars): {response.text[:1000]}")
                    return []
            else:
                # If API call fails, log the error
                error_text = response.text[:500] if response.text else "No error message"
                print(f"[OllamaProvider.get_available_models] ✗ Error: Ollama API returned status {response.status_code}")
                print(f"[OllamaProvider.get_available_models] Error response: {error_text}")
                return []
        
        except requests.exceptions.Timeout as e:
            print(f"[OllamaProvider.get_available_models] ✗ Timeout error connecting to Ollama at {self.tags_endpoint}")
            print(f"[OllamaProvider.get_available_models] Timeout details: {str(e)}")
            return []
        except requests.exceptions.ConnectionError as e:
            print(f"[OllamaProvider.get_available_models] ✗ Connection error to Ollama at {self.tags_endpoint}")
            print(f"[OllamaProvider.get_available_models] Connection error details: {str(e)}")
            print(f"[OllamaProvider.get_available_models] Error type: {type(e).__name__}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[OllamaProvider.get_available_models] ✗ Request exception when fetching Ollama models")
            print(f"[OllamaProvider.get_available_models] Request exception details: {str(e)}")
            print(f"[OllamaProvider.get_available_models] Exception type: {type(e).__name__}")
            return []
        except Exception as e:
            print(f"[OllamaProvider.get_available_models] ✗ Unexpected error when fetching Ollama models")
            print(f"[OllamaProvider.get_available_models] Error: {str(e)}")
            print(f"[OllamaProvider.get_available_models] Exception type: {type(e).__name__}")
            import traceback
            print(f"[OllamaProvider.get_available_models] Full traceback:")
            traceback.print_exc()
            return []
    
    def get_default_model(self) -> str:
        """
        Get default model (prefers smaller models to avoid memory issues)
        
        Returns:
            Default model name (preferring smaller models)
        """
        available_models = self.get_available_models()
        
        if available_models:
            # Sort models by estimated size (smallest first) to prefer smaller models
            # This helps avoid CUDA_Host buffer allocation errors
            sorted_models = sorted(
                available_models,
                key=lambda m: self._estimate_model_size(m)
            )
            preferred_model = sorted_models[0]
            print(f"[OllamaProvider.get_default_model] Selected model: {preferred_model} (estimated {self._estimate_model_size(preferred_model)}B params)")
            print(f"[OllamaProvider.get_default_model] Available models sorted by size: {[(m, self._estimate_model_size(m)) for m in sorted_models[:5]]}")
            return preferred_model
        
        # Fallback model if API is unavailable
        print(f"[OllamaProvider.get_default_model] No models available, using fallback: llama3.2:1b")
        return "llama3.2:1b"
    
    def generate_response_with_messages(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> str:
        """
        Generate a non-streaming response from Ollama using conversation history
        
        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'
            model: Optional specific model to use
        
        Returns:
            The generated response text
        
        Raises:
            Exception: If generation fails
        """
        selected_model = model or self.get_default_model()
        
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            # Ollama expects 'role' and 'content' (already in correct format)
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        request_body = {
            "model": selected_model,
            "messages": ollama_messages,
            "stream": False
        }
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=request_body,
                headers={"Content-Type": "application/json"},
                timeout=120  # Longer timeout for AI generation
            )
            
            if response.status_code == 200:
                data = response.json()
                # Ollama chat API returns message in 'message' field with 'content'
                message = data.get("message", {})
                return message.get("content", "")
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", f"Ollama API error: {response.status_code}")
                
                # Check for memory-related errors
                error_lower = error_msg.lower()
                if any(keyword in error_lower for keyword in ["memory", "buffer", "allocate", "cuda", "out of memory"]):
                    raise Exception(
                        f"Memory error loading model '{selected_model}': {error_msg}. "
                        f"Try using a smaller model. Available models: {', '.join(self.get_available_models()[:5])}"
                    )
                
                raise Exception(error_msg)
        
        except requests.exceptions.RequestException as e:
            error_str = str(e)
            # Check for memory-related connection errors
            if "buffer" in error_str.lower() or "allocate" in error_str.lower():
                raise Exception(
                    f"Memory allocation error with model '{selected_model}': {error_str}. "
                    f"Try using a smaller model."
                )
            raise Exception(f"Failed to connect to Ollama: {error_str}")
    
    def stream_response_with_messages(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from Ollama using conversation history
        
        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'
            model: Optional specific model to use
        
        Yields:
            Chunks of the generated response text
        
        Raises:
            Exception: If streaming fails
        """
        selected_model = model or self.get_default_model()
        
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            # Ollama expects 'role' and 'content' (already in correct format)
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        request_body = {
            "model": selected_model,
            "messages": ollama_messages,
            "stream": True
        }
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=request_body,
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=120
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", f"Ollama API error: {response.status_code}")
                
                # Check for memory-related errors
                error_lower = error_msg.lower()
                if any(keyword in error_lower for keyword in ["memory", "buffer", "allocate", "cuda", "out of memory"]):
                    raise Exception(
                        f"Memory error loading model '{selected_model}': {error_msg}. "
                        f"Try using a smaller model. Available models: {', '.join(self.get_available_models()[:5])}"
                    )
                
                raise Exception(error_msg)
            
            # Stream the response
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line.decode('utf-8'))
                        # Ollama chat API returns chunks in 'message.content' field
                        message = chunk_data.get("message", {})
                        chunk_text = message.get("content", "")
                        if chunk_text:
                            yield chunk_text
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
        
        except requests.exceptions.RequestException as e:
            error_str = str(e)
            # Check for memory-related connection errors
            if "buffer" in error_str.lower() or "allocate" in error_str.lower():
                raise Exception(
                    f"Memory allocation error with model '{selected_model}': {error_str}. "
                    f"Try using a smaller model."
                )
            raise Exception(f"Failed to connect to Ollama: {error_str}")

