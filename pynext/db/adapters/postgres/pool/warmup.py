"""
PostgreSQL Connection Warmup.

This module provides connection warmup functionality to eliminate cold-start
latency. It follows SolidJS principles:
- Eager: Warm connections before they're needed
- Parallel: Warm multiple connections simultaneously
- Observable: Know exactly what's warming and when

How Warmup Works:

1. When pool starts, run warmup query on all initial connections
2. When new connection is created, optionally warm it
3. Warmup query exercises the connection path (network, auth, etc.)
4. Optionally prepare frequently-used statements

Why This Matters:
- First query on cold connection is slow (TLS handshake, auth, etc.)
- Warmup moves that latency to startup time
- Production traffic gets fast connections from the start

AI-Friendly Design:
- Simple config: warmup=True is all you need
- Customizable warmup queries for advanced use
- Clear logging of warmup progress
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg

logger = logging.getLogger("pynext.db.postgres.warmup")


@dataclass
class WarmupConfig:
    """Configuration for connection warmup.
    
    Attributes:
        enabled: Whether warmup is enabled (default: True)
        query: Query to run for warmup (default: "SELECT 1")
        timeout: Timeout for warmup query in seconds (default: 5.0)
        parallel: Whether to warm connections in parallel (default: True)
        max_parallel: Maximum parallel warmup operations (default: 10)
        prepare_statements: Statements to prepare during warmup (default: [])
        retry_on_failure: Whether to retry failed warmup (default: True)
        max_retries: Maximum number of warmup retries (default: 3)
        retry_delay: Delay between retries in seconds (default: 0.5)
        on_warmup_start: Callback when warmup starts (default: None)
        on_warmup_complete: Callback when warmup completes (default: None)
    
    Example:
        config = WarmupConfig(
            enabled=True,
            query="SELECT 1",
            timeout=5.0,
            parallel=True,
        )
        
        # Advanced: Prepare common statements
        config = WarmupConfig(
            prepare_statements=[
                "SELECT * FROM users WHERE id = $1",
                "SELECT * FROM posts WHERE user_id = $1",
            ]
        )
    """
    enabled: bool = True
    query: str = "SELECT 1"
    timeout: float = 5.0
    parallel: bool = True
    max_parallel: int = 10
    prepare_statements: List[str] = field(default_factory=list)
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_delay: float = 0.5
    on_warmup_start: Optional[Callable[[], None]] = None
    on_warmup_complete: Optional[Callable[[int, int, float], None]] = None
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.timeout <= 0:
            raise ValueError(f"timeout must be > 0, got {self.timeout}")
        if self.max_parallel < 1:
            raise ValueError(f"max_parallel must be >= 1, got {self.max_parallel}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")
        if self.retry_delay < 0:
            raise ValueError(f"retry_delay must be >= 0, got {self.retry_delay}")


@dataclass
class WarmupResult:
    """Result of a connection warmup operation.
    
    Attributes:
        connection_id: ID of the connection that was warmed
        success: Whether warmup succeeded
        duration_ms: Time taken for warmup in milliseconds
        error: Error message if warmup failed
        retries: Number of retries needed
    """
    connection_id: str
    success: bool
    duration_ms: float
    error: Optional[str] = None
    retries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "connection_id": self.connection_id,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "retries": self.retries,
        }


@dataclass
class WarmupStats:
    """Statistics about warmup operations.
    
    Attributes:
        total_warmups: Total warmup operations performed
        successful_warmups: Number of successful warmups
        failed_warmups: Number of failed warmups
        total_retries: Total number of retries across all warmups
        total_duration_ms: Total time spent warming connections
        avg_duration_ms: Average warmup time in milliseconds
    """
    total_warmups: int = 0
    successful_warmups: int = 0
    failed_warmups: int = 0
    total_retries: int = 0
    total_duration_ms: float = 0
    warmup_durations: List[float] = field(default_factory=list)
    
    @property
    def avg_duration_ms(self) -> float:
        """Average warmup duration in milliseconds."""
        if not self.warmup_durations:
            return 0
        return sum(self.warmup_durations) / len(self.warmup_durations)
    
    @property
    def success_rate(self) -> float:
        """Warmup success rate (0.0 to 1.0)."""
        if self.total_warmups == 0:
            return 1.0
        return self.successful_warmups / self.total_warmups
    
    def record(self, result: WarmupResult) -> None:
        """Record a warmup result."""
        self.total_warmups += 1
        self.total_retries += result.retries
        
        if result.success:
            self.successful_warmups += 1
            self.total_duration_ms += result.duration_ms
            self.warmup_durations.append(result.duration_ms)
            
            # Keep only last 1000 for memory efficiency
            if len(self.warmup_durations) > 1000:
                self.warmup_durations.pop(0)
        else:
            self.failed_warmups += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "total_warmups": self.total_warmups,
            "successful_warmups": self.successful_warmups,
            "failed_warmups": self.failed_warmups,
            "success_rate": self.success_rate,
            "total_retries": self.total_retries,
            "avg_duration_ms": self.avg_duration_ms,
        }


class ConnectionWarmer:
    """Warms up database connections to eliminate cold-start latency.
    
    This class handles running warmup queries on connections to ensure
    they're ready for immediate use. It can warm connections:
    
    1. **At pool startup**: Warm all initial connections
    2. **On new connection**: Warm newly created connections
    3. **Periodically**: Re-warm idle connections
    
    Basic Usage:
        warmer = ConnectionWarmer(WarmupConfig())
        
        # Warm a single connection
        result = await warmer.warmup_connection("conn_1", connection)
        
        # Warm multiple connections in parallel
        results = await warmer.warmup_all(connections)
    
    With Statement Preparation:
        warmer = ConnectionWarmer(WarmupConfig(
            prepare_statements=[
                "SELECT * FROM users WHERE id = $1",
                "SELECT * FROM posts WHERE user_id = $1",
            ]
        ))
        
        # Warmup now also prepares these statements
        await warmer.warmup_connection("conn_1", connection)
    """
    
    def __init__(self, config: Optional[WarmupConfig] = None):
        """Initialize the warmer.
        
        Args:
            config: Warmup configuration (default: WarmupConfig())
        """
        self._config = config or WarmupConfig()
        self._stats = WarmupStats()
        self._statement_names: Dict[str, str] = {}  # statement -> name mapping
    
    @property
    def config(self) -> WarmupConfig:
        """Get warmup configuration."""
        return self._config
    
    @property
    def enabled(self) -> bool:
        """Check if warmup is enabled."""
        return self._config.enabled
    
    async def warmup_connection(
        self,
        connection_id: str,
        connection: "asyncpg.Connection",
    ) -> WarmupResult:
        """Warm up a single connection.
        
        Runs the warmup query and optionally prepares statements.
        
        Args:
            connection_id: ID of the connection
            connection: The asyncpg connection to warm
        
        Returns:
            WarmupResult with success/failure and timing info
        
        Example:
            result = await warmer.warmup_connection("conn_1", conn)
            if result.success:
                print(f"Warmed in {result.duration_ms:.1f}ms")
        """
        if not self._config.enabled:
            return WarmupResult(
                connection_id=connection_id,
                success=True,
                duration_ms=0,
            )
        
        start_time = time.monotonic()
        retries = 0
        last_error = None
        
        for attempt in range(self._config.max_retries + 1):
            try:
                # Run warmup query
                await asyncio.wait_for(
                    connection.fetchval(self._config.query),
                    timeout=self._config.timeout,
                )
                
                # Prepare statements if configured
                if self._config.prepare_statements:
                    await self._prepare_statements(connection)
                
                duration_ms = (time.monotonic() - start_time) * 1000
                
                result = WarmupResult(
                    connection_id=connection_id,
                    success=True,
                    duration_ms=duration_ms,
                    retries=retries,
                )
                self._stats.record(result)
                
                logger.debug(
                    f"Warmed connection {connection_id} in {duration_ms:.1f}ms "
                    f"(retries: {retries})"
                )
                
                return result
                
            except asyncio.TimeoutError:
                last_error = "warmup query timed out"
                retries += 1
                logger.warning(
                    f"Warmup timeout for {connection_id} (attempt {attempt + 1})"
                )
                
            except Exception as e:
                last_error = str(e)
                retries += 1
                logger.warning(
                    f"Warmup failed for {connection_id}: {e} (attempt {attempt + 1})"
                )
            
            # Retry if configured
            if (
                self._config.retry_on_failure
                and attempt < self._config.max_retries
            ):
                await asyncio.sleep(self._config.retry_delay)
        
        # All retries failed
        duration_ms = (time.monotonic() - start_time) * 1000
        result = WarmupResult(
            connection_id=connection_id,
            success=False,
            duration_ms=duration_ms,
            error=last_error,
            retries=retries,
        )
        self._stats.record(result)
        
        logger.error(
            f"Warmup failed for {connection_id} after {retries} retries: {last_error}"
        )
        
        return result
    
    async def warmup_all(
        self,
        connections: Dict[str, "asyncpg.Connection"],
    ) -> List[WarmupResult]:
        """Warm up multiple connections.
        
        If parallel is enabled, warms connections concurrently up to max_parallel.
        Otherwise, warms them sequentially.
        
        Args:
            connections: Mapping of connection ID to asyncpg connection
        
        Returns:
            List of WarmupResult for each connection
        
        Example:
            results = await warmer.warmup_all({
                "conn_1": conn1,
                "conn_2": conn2,
            })
            
            successful = sum(1 for r in results if r.success)
            print(f"Warmed {successful}/{len(results)} connections")
        """
        if not self._config.enabled or not connections:
            return []
        
        start_time = time.monotonic()
        
        if self._config.on_warmup_start:
            self._config.on_warmup_start()
        
        logger.info(f"Starting warmup for {len(connections)} connections")
        
        if self._config.parallel:
            results = await self._warmup_parallel(connections)
        else:
            results = await self._warmup_sequential(connections)
        
        duration_s = time.monotonic() - start_time
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        if self._config.on_warmup_complete:
            self._config.on_warmup_complete(successful, failed, duration_s)
        
        logger.info(
            f"Warmup complete: {successful}/{len(results)} successful "
            f"in {duration_s:.2f}s"
        )
        
        return results
    
    async def _warmup_parallel(
        self,
        connections: Dict[str, "asyncpg.Connection"],
    ) -> List[WarmupResult]:
        """Warm connections in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(self._config.max_parallel)
        
        async def warm_with_limit(conn_id: str, conn: "asyncpg.Connection"):
            async with semaphore:
                return await self.warmup_connection(conn_id, conn)
        
        tasks = [
            warm_with_limit(conn_id, conn)
            for conn_id, conn in connections.items()
        ]
        
        return await asyncio.gather(*tasks)
    
    async def _warmup_sequential(
        self,
        connections: Dict[str, "asyncpg.Connection"],
    ) -> List[WarmupResult]:
        """Warm connections sequentially."""
        results = []
        for conn_id, conn in connections.items():
            result = await self.warmup_connection(conn_id, conn)
            results.append(result)
        return results
    
    async def _prepare_statements(
        self,
        connection: "asyncpg.Connection",
    ) -> None:
        """Prepare frequently-used statements on a connection."""
        for i, statement in enumerate(self._config.prepare_statements):
            try:
                # Generate a unique name for this statement
                name = f"pynext_warmup_{i}"
                await connection.prepare(statement, name=name)
                self._statement_names[statement] = name
                logger.debug(f"Prepared statement: {name}")
            except Exception as e:
                logger.warning(f"Failed to prepare statement: {e}")
    
    def get_stats(self) -> WarmupStats:
        """Get warmup statistics.
        
        Returns:
            WarmupStats with current values
        """
        return self._stats
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ConnectionWarmer("
            f"enabled={self._config.enabled}, "
            f"warmups={self._stats.total_warmups}, "
            f"success_rate={self._stats.success_rate:.1%})"
        )

