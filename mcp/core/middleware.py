"""MCP middleware for security, rate limiting, and logging."""
from typing import Dict, Any, Optional, Callable
import time
import re
import structlog

from mcp.core.protocol.messages import JSONRPCRequest
from mcp.core.concurrency import RateLimiter
from mcp.core.concurrency import CancellationToken

logger = structlog.get_logger(__name__)


class Middleware:
    """Base middleware interface."""
    
    async def __call__(
        self,
        request: JSONRPCRequest,
        handler: Callable
    ) -> Any:
        """Execute middleware."""
        return await handler(request.params or {}, None)


class LoggingMiddleware(Middleware):
    """Logging middleware."""
    
    def __init__(self, log_requests: bool = True, log_responses: bool = False):
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def __call__(
        self,
        request: JSONRPCRequest,
        handler: Callable
    ) -> Any:
        """Log request and response."""
        request_id = str(request.id) if request.id else "notification"
        start_time = time.time()
        
        if self.log_requests:
            logger.info(
                "Request received",
                request_id=request_id,
                method=request.method,
                params_size=len(str(request.params or {}))
            )
        
        try:
            result = await handler(request.params or {}, None)
            duration_ms = (time.time() - start_time) * 1000
            
            if self.log_responses:
                logger.info(
                    "Request completed",
                    request_id=request_id,
                    method=request.method,
                    duration_ms=duration_ms,
                    status="success"
                )
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                duration_ms=duration_ms,
                error=str(e),
                status="error"
            )
            raise


class RateLimitMiddleware(Middleware):
    """Rate limiting middleware."""
    
    def __init__(
        self,
        default_rate: float = 100.0,  # requests per minute
        default_capacity: int = 10,
        method_limits: Optional[Dict[str, Dict[str, float]]] = None
    ):
        self.default_rate = default_rate / 60.0  # Convert to per second
        self.default_capacity = default_capacity
        self.method_limits = method_limits or {}
        
        # Create rate limiters per method
        self.limiters: Dict[str, RateLimiter] = {}
        for method, limits in self.method_limits.items():
            rate = limits.get("rate", default_rate) / 60.0
            capacity = int(limits.get("capacity", default_capacity))
            self.limiters[method] = RateLimiter(rate, capacity)
    
    def _get_limiter(self, method: str) -> RateLimiter:
        """Get rate limiter for method."""
        if method not in self.limiters:
            self.limiters[method] = RateLimiter(
                self.default_rate,
                self.default_capacity
            )
        return self.limiters[method]
    
    async def __call__(
        self,
        request: JSONRPCRequest,
        handler: Callable
    ) -> Any:
        """Apply rate limiting."""
        limiter = self._get_limiter(request.method)
        
        if not await limiter.acquire():
            raise RuntimeError(
                f"Rate limit exceeded for method: {request.method}"
            )
        
        return await handler(request.params or {}, None)


class SecretsRedactionMiddleware(Middleware):
    """Secrets redaction middleware for logs."""
    
    def __init__(self):
        # Patterns for common secrets
        self.patterns = [
            (r'api[_-]?key["\s]*[:=]\s*["\']?([^\s"\']+)', r'api_key="***REDACTED***"'),
            (r'token["\s]*[:=]\s*["\']?([^\s"\']+)', r'token="***REDACTED***"'),
            (r'password["\s]*[:=]\s*["\']?([^\s"\']+)', r'password="***REDACTED***"'),
            (r'secret["\s]*[:=]\s*["\']?([^\s"\']+)', r'secret="***REDACTED***"'),
            (r'("(api_key|token|password|secret)":\s*)"[^"]+"', r'\1"***REDACTED***"'),
        ]
    
    def redact(self, text: str) -> str:
        """Redact secrets from text."""
        result = text
        for pattern, replacement in self.patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    
    async def __call__(
        self,
        request: JSONRPCRequest,
        handler: Callable
    ) -> Any:
        """Redact secrets from request/response."""
        # Redact params if present
        if request.params:
            params_str = str(request.params)
            redacted_params = self.redact(params_str)
            if redacted_params != params_str:
                logger.debug(
                    "Secrets redacted",
                    method=request.method,
                    params_redacted=True
                )
        
        result = await handler(request.params or {}, None)
        
        # Redact result if it's a string
        if isinstance(result, str):
            result = self.redact(result)
        
        return result


class AuthMiddleware(Middleware):
    """Authentication middleware."""
    
    def __init__(self, enabled: bool = False, token_file: Optional[str] = None):
        self.enabled = enabled
        self.token_file = token_file
        self.tokens: Dict[str, str] = {}
        
        if enabled and token_file:
            self._load_tokens()
    
    def _load_tokens(self):
        """Load tokens from file."""
        try:
            with open(self.token_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line:
                            client_id, token = line.split(':', 1)
                            self.tokens[client_id] = token
        except FileNotFoundError:
            logger.warn("Token file not found", file=self.token_file)
        except Exception as e:
            logger.error("Error loading tokens", error=str(e))
    
    async def __call__(
        self,
        request: JSONRPCRequest,
        handler: Callable
    ) -> Any:
        """Check authentication."""
        if not self.enabled:
            return await handler(request.params or {}, None)
        
        # Extract token from params or headers (simplified)
        # In production, use proper header extraction
        auth_token = request.params.get("_auth_token") if request.params else None
        
        if not auth_token:
            raise PermissionError("Authentication required")
        
        # Validate token (simplified)
        # In production, use proper token validation
        if auth_token not in self.tokens.values():
            raise PermissionError("Invalid authentication token")
        
        return await handler(request.params or {}, None)

