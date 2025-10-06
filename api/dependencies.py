from functools import lru_cache
from typing import Optional
import logging
from fastapi import Depends, HTTPException, Header
from agent.agentic_workflow import GraphBuilder
from core.config import get_settings

logger = logging.getLogger(__name__)

# Cache for graph builder instance to avoid recreating it for every request
@lru_cache()
def get_graph_builder(model_provider: str = "groq") -> GraphBuilder:
    """
    Get or create a GraphBuilder instance
    
    Args:
        model_provider: The model provider to use (groq or openai)
        
    Returns:
        GraphBuilder instance
    """
    try:
        logger.info(f"Creating GraphBuilder with provider: {model_provider}")
        return GraphBuilder(model_provider=model_provider)
    except Exception as e:
        logger.error(f"Failed to create GraphBuilder: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize AI agent. Please try again later."
        )

def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current user from authorization header (optional for now)
    
    In a production environment, you would validate the JWT token here
    """
    # For now, we'll make this optional
    # In production, implement proper JWT validation
    return {"user_id": "anonymous", "is_authenticated": False}

def validate_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """
    Validate API key if provided
    
    Args:
        x_api_key: API key from header
    
    Returns:
        bool: True if valid or no key provided
    """
    settings = get_settings()
    
    # If no API key is configured, allow all requests
    if not settings.API_KEY:
        return True
    
    # If API key is configured but not provided, reject
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
    
    # Validate the API key
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return True

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, client_ip: str, limit: int = 60) -> bool:
        """
        Check if request is allowed based on rate limit
        
        Args:
            client_ip: Client IP address
            limit: Requests per minute limit
            
        Returns:
            bool: True if allowed
        """
        import time
        
        current_time = time.time()
        minute_window = int(current_time // 60)
        
        key = f"{client_ip}:{minute_window}"
        
        if key not in self.requests:
            self.requests[key] = 0
        
        if self.requests[key] >= limit:
            return False
        
        self.requests[key] += 1
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        return True
    
    def _cleanup_old_entries(self, current_time: float):
        """Clean up old rate limit entries"""
        current_minute = int(current_time // 60)
        keys_to_remove = []
        
        for key in self.requests:
            minute = int(key.split(':')[1])
            if current_minute - minute > 5:  # Keep 5 minutes of history
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.requests[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(client_ip: str = Header(None, alias="x-real-ip")):
    """
    Check rate limit for the client
    
    Args:
        client_ip: Client IP address
    """
    if not client_ip:
        # Fallback if no IP is provided
        client_ip = "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return True

def get_request_context():
    """
    Get request context for logging and analytics
    """
    import time
    return {
        "timestamp": time.time(),
        "request_id": f"req_{int(time.time() * 1000)}"
    }