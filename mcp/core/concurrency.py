"""Concurrency management and backpressure."""
import asyncio
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime, timedelta
import uuid

from mcp.core.errors import MCPTimeoutError, MCPCancelledError


class CancellationToken:
    """Token for request cancellation."""
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.cancelled = False
        self.cancelled_at: Optional[datetime] = None
    
    def cancel(self):
        """Cancel the request."""
        self.cancelled = True
        self.cancelled_at = datetime.utcnow()
    
    def check(self):
        """Raise if cancelled."""
        if self.cancelled:
            raise MCPCancelledError(self.request_id)


class RequestTracker:
    """Tracks in-flight requests."""
    def __init__(self, max_concurrent: int = 32):
        self.max_concurrent = max_concurrent
        self.active_requests: Dict[str, CancellationToken] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def acquire(self, request_id: str) -> CancellationToken:
        """Acquire a slot for a new request."""
        await self.semaphore.acquire()
        token = CancellationToken(request_id)
        self.active_requests[request_id] = token
        return token
    
    def release(self, request_id: str):
        """Release a slot."""
        if request_id in self.active_requests:
            del self.active_requests[request_id]
        self.semaphore.release()
    
    def cancel(self, request_id: str) -> bool:
        """Cancel a request if active."""
        if request_id in self.active_requests:
            self.active_requests[request_id].cancel()
            return True
        return False
    
    def is_full(self) -> bool:
        """Check if at capacity."""
        return len(self.active_requests) >= self.max_concurrent
    
    def active_count(self) -> int:
        """Get number of active requests."""
        return len(self.active_requests)


class RateLimiter:
    """Token bucket rate limiter."""
    def __init__(self, rate: float, capacity: int):
        """Initialize rate limiter.
        
        Args:
            rate: Tokens per second
            capacity: Maximum token bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_update = datetime.utcnow()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False if rate limited
        """
        async with self._lock:
            now = datetime.utcnow()
            elapsed = (now - self.last_update).total_seconds()
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class TimeoutManager:
    """Manages request timeouts."""
    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout
    
    async def execute_with_timeout(
        self,
        coro: Callable,
        timeout: Optional[float] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        """Execute coroutine with timeout.
        
        Args:
            coro: Coroutine to execute
            timeout: Timeout in seconds (uses default if None)
            cancellation_token: Optional cancellation token
            
        Returns:
            Coroutine result
            
        Raises:
            MCPTimeoutError: If timeout exceeded
            MCPCancelledError: If cancelled
        """
        timeout = timeout or self.default_timeout
        
        try:
            return await asyncio.wait_for(coro(), timeout=timeout)
        except asyncio.TimeoutError:
            raise MCPTimeoutError("request", timeout)
        except MCPCancelledError:
            raise
        except Exception as e:
            # Re-raise other exceptions
            raise


class BackpressureController:
    """Controls backpressure for request processing."""
    def __init__(
        self,
        max_queue_size: int = 100,
        max_concurrent: int = 32,
        queue_timeout: float = 5.0
    ):
        self.max_queue_size = max_queue_size
        self.max_concurrent = max_concurrent
        self.queue_timeout = queue_timeout
        self.request_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.request_tracker = RequestTracker(max_concurrent)
    
    async def enqueue(
        self,
        request_id: str,
        handler: Callable,
        timeout: Optional[float] = None
    ) -> Any:
        """Enqueue a request for processing.
        
        Args:
            request_id: Request identifier
            handler: Async handler function
            timeout: Optional timeout
            
        Returns:
            Handler result
        """
        # Check if queue is full
        if self.request_queue.full():
            raise RuntimeError("Request queue is full")
        
        # Create future for result
        future = asyncio.Future()
        
        # Put request in queue
        await asyncio.wait_for(
            self.request_queue.put((request_id, handler, future, timeout)),
            timeout=self.queue_timeout
        )
        
        # Wait for result
        try:
            result = await future
            return result
        except asyncio.CancelledError:
            # Cancel if future was cancelled
            self.request_tracker.cancel(request_id)
            raise MCPCancelledError(request_id)

