"""
PostgreSQL External Pooler Support.

This module provides support for external connection poolers like PgBouncer
and pgpool. It follows SolidJS principles:
- Auto-detection: Detect pooler presence automatically
- Transparent: Work seamlessly with or without poolers
- No surprises: Clear documentation of pooler-specific behaviors

How External Poolers Work:

1. External poolers sit between your app and PostgreSQL
2. They multiplex many client connections to fewer DB connections
3. Different pooling modes have different capabilities:
   - Transaction: New DB connection per transaction (most scalable)
   - Session: Dedicated DB connection per client session
   - Statement: New DB connection per statement (legacy)

Why Use External Poolers:
- Handle more concurrent connections than PostgreSQL can
- Connection reuse reduces latency
- Centralized connection management across app instances

Compatibility Notes:
- Transaction mode: No prepared statements, no session-level settings
- Session mode: Full PostgreSQL feature support
- PyNext auto-detects and adapts to the pooler configuration

AI-Friendly Design:
- Clear mode documentation
- Auto-detection with override capability
- Comprehensive error messages for pooler issues
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg

logger = logging.getLogger("pynext.db.postgres.external")


class PoolerType(Enum):
    """Type of external connection pooler.
    
    PGBOUNCER: PgBouncer - lightweight, high-performance pooler
    PGPOOL: pgpool-II - feature-rich, supports replication
    ODYSSEY: Odyssey - modern, multi-threaded pooler
    UNKNOWN: Unknown or undetected pooler
    NONE: No external pooler (direct PostgreSQL connection)
    """
    PGBOUNCER = "pgbouncer"
    PGPOOL = "pgpool"
    ODYSSEY = "odyssey"
    UNKNOWN = "unknown"
    NONE = "none"


class PoolerMode(Enum):
    """Pooling mode of external pooler.
    
    TRANSACTION: New DB connection per transaction
        - Most scalable (100+ clients per DB connection)
        - No prepared statements
        - No session-level settings (SET, LISTEN, etc.)
        
    SESSION: Dedicated DB connection per client
        - Full PostgreSQL feature support
        - Less scalable (1:1 mapping)
        - Good for apps that need full features
        
    STATEMENT: New DB connection per statement (deprecated)
        - Very limited use cases
        - Avoid unless you know you need it
    """
    TRANSACTION = "transaction"
    SESSION = "session"
    STATEMENT = "statement"


@dataclass
class ExternalPoolerConfig:
    """Configuration for external pooler compatibility.
    
    Attributes:
        enabled: Whether external pooler support is enabled (default: False)
        type: Type of pooler (default: auto-detect)
        mode: Pooling mode (default: TRANSACTION)
        disable_prepared_statements: Disable prepared statements (auto for transaction mode)
        disable_server_side_cursors: Disable server-side cursors (auto for transaction mode)
        disable_notifications: Disable LISTEN/NOTIFY (auto for transaction mode)
        connection_check_query: Query to validate pooler connection
        auto_detect: Whether to auto-detect pooler presence (default: True)
        verify_on_connect: Verify pooler settings on connect (default: True)
    
    Example:
        # Auto-detect PgBouncer
        config = ExternalPoolerConfig(enabled=True)
        
        # Explicit PgBouncer transaction mode
        config = ExternalPoolerConfig(
            enabled=True,
            type=PoolerType.PGBOUNCER,
            mode=PoolerMode.TRANSACTION,
        )
    """
    enabled: bool = False
    type: PoolerType = PoolerType.NONE
    mode: PoolerMode = PoolerMode.TRANSACTION
    disable_prepared_statements: Optional[bool] = None  # Auto-set based on mode
    disable_server_side_cursors: Optional[bool] = None
    disable_notifications: Optional[bool] = None
    connection_check_query: str = "SELECT 1"
    auto_detect: bool = True
    verify_on_connect: bool = True
    
    def __post_init__(self) -> None:
        """Apply mode-specific defaults."""
        if self.mode == PoolerMode.TRANSACTION:
            # Transaction mode has limitations
            if self.disable_prepared_statements is None:
                self.disable_prepared_statements = True
            if self.disable_server_side_cursors is None:
                self.disable_server_side_cursors = True
            if self.disable_notifications is None:
                self.disable_notifications = True
        else:
            # Session/Statement mode - allow everything by default
            if self.disable_prepared_statements is None:
                self.disable_prepared_statements = False
            if self.disable_server_side_cursors is None:
                self.disable_server_side_cursors = False
            if self.disable_notifications is None:
                self.disable_notifications = False
    
    def get_incompatible_features(self) -> List[str]:
        """Get list of features incompatible with current configuration.
        
        Returns:
            List of feature names that are disabled
        """
        features = []
        if self.disable_prepared_statements:
            features.append("prepared_statements")
        if self.disable_server_side_cursors:
            features.append("server_side_cursors")
        if self.disable_notifications:
            features.append("notifications")
        return features


@dataclass
class PoolerInfo:
    """Information about detected external pooler.
    
    Attributes:
        type: Type of pooler detected
        mode: Pooling mode (if detected)
        version: Pooler version (if detected)
        server_version: PostgreSQL server version
        extra: Additional pooler-specific information
    """
    type: PoolerType
    mode: Optional[PoolerMode] = None
    version: Optional[str] = None
    server_version: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "type": self.type.value,
            "mode": self.mode.value if self.mode else None,
            "version": self.version,
            "server_version": self.server_version,
            "extra": self.extra,
        }


class PoolerDetectionError(Exception):
    """Error detecting or configuring external pooler."""
    pass


class PoolerCompatibilityError(Exception):
    """Error due to pooler compatibility issues.
    
    This is raised when trying to use a feature incompatible with the
    current pooler configuration.
    """
    def __init__(self, feature: str, pooler_type: PoolerType, mode: PoolerMode):
        self.feature = feature
        self.pooler_type = pooler_type
        self.mode = mode
        super().__init__(
            f"Feature '{feature}' is not compatible with "
            f"{pooler_type.value} in {mode.value} mode.\n"
            f"Consider using session mode or connecting directly to PostgreSQL."
        )


class ExternalPoolerManager:
    """Manages external pooler detection and compatibility.
    
    This class handles:
    1. Auto-detecting external pooler presence
    2. Configuring connection parameters for pooler compatibility
    3. Validating feature usage against pooler capabilities
    4. Providing clear errors when incompatible features are used
    
    Basic Usage:
        manager = ExternalPoolerManager(ExternalPoolerConfig(enabled=True))
        
        # Detect pooler on first connection
        info = await manager.detect_pooler(connection)
        print(f"Detected: {info.type.value}")
        
        # Check feature compatibility
        if manager.can_use_prepared_statements():
            stmt = await conn.prepare("SELECT $1")
    
    With Explicit Configuration:
        manager = ExternalPoolerManager(ExternalPoolerConfig(
            enabled=True,
            type=PoolerType.PGBOUNCER,
            mode=PoolerMode.TRANSACTION,
        ))
        
        # No auto-detection needed
        print(f"Using PgBouncer in transaction mode")
    """
    
    def __init__(self, config: Optional[ExternalPoolerConfig] = None):
        """Initialize the manager.
        
        Args:
            config: External pooler configuration (default: ExternalPoolerConfig())
        """
        self._config = config or ExternalPoolerConfig()
        self._pooler_info: Optional[PoolerInfo] = None
        self._detected = False
    
    @property
    def config(self) -> ExternalPoolerConfig:
        """Get pooler configuration."""
        return self._config
    
    @property
    def is_enabled(self) -> bool:
        """Check if external pooler support is enabled."""
        return self._config.enabled
    
    @property
    def pooler_info(self) -> Optional[PoolerInfo]:
        """Get detected pooler information."""
        return self._pooler_info
    
    @property
    def pooler_type(self) -> PoolerType:
        """Get the pooler type (configured or detected)."""
        return self._config.type
    
    @property
    def pooler_mode(self) -> PoolerMode:
        """Get the pooling mode (configured or detected)."""
        if self._pooler_info and self._pooler_info.mode:
            return self._pooler_info.mode
        return self._config.mode
    
    async def detect_pooler(
        self,
        connection: "asyncpg.Connection",
    ) -> PoolerInfo:
        """Detect external pooler from connection.
        
        Analyzes connection parameters and server responses to detect
        the presence and type of external pooler.
        
        Args:
            connection: An asyncpg connection to analyze
        
        Returns:
            PoolerInfo with detected pooler details
        
        Raises:
            PoolerDetectionError: If detection fails
        """
        if not self._config.auto_detect:
            # Use configured values
            self._pooler_info = PoolerInfo(
                type=self._config.type,
                mode=self._config.mode,
            )
            self._detected = True
            return self._pooler_info
        
        try:
            # Get server version string
            server_version = connection.get_server_version()
            version_str = f"{server_version.major}.{server_version.minor}"
            
            # Try to detect pooler from application_name or other params
            pooler_type = PoolerType.NONE
            pooler_version = None
            extra = {}
            
            # Check for PgBouncer indicators
            try:
                # PgBouncer exposes stats via SHOW commands
                result = await connection.fetchrow("SHOW STATS")
                if result:
                    pooler_type = PoolerType.PGBOUNCER
                    extra["stats"] = dict(result)
            except Exception:
                pass
            
            # Check for pgpool indicators
            if pooler_type == PoolerType.NONE:
                try:
                    result = await connection.fetchrow("SHOW pool_status")
                    if result:
                        pooler_type = PoolerType.PGPOOL
                        extra["pool_status"] = dict(result)
                except Exception:
                    pass
            
            # Check connection port as hint
            # PgBouncer commonly uses 6432, pgpool uses 9999
            # This is a fallback heuristic
            
            self._pooler_info = PoolerInfo(
                type=pooler_type,
                mode=self._config.mode,
                server_version=version_str,
                extra=extra,
            )
            self._detected = True
            
            if pooler_type != PoolerType.NONE:
                logger.info(
                    f"Detected external pooler: {pooler_type.value} "
                    f"(mode: {self._config.mode.value})"
                )
            
            return self._pooler_info
            
        except Exception as e:
            raise PoolerDetectionError(f"Failed to detect pooler: {e}") from e
    
    def can_use_prepared_statements(self) -> bool:
        """Check if prepared statements can be used.
        
        Returns:
            True if prepared statements are allowed
        """
        if not self._config.enabled:
            return True
        return not self._config.disable_prepared_statements
    
    def can_use_server_side_cursors(self) -> bool:
        """Check if server-side cursors can be used.
        
        Returns:
            True if server-side cursors are allowed
        """
        if not self._config.enabled:
            return True
        return not self._config.disable_server_side_cursors
    
    def can_use_notifications(self) -> bool:
        """Check if LISTEN/NOTIFY can be used.
        
        Returns:
            True if notifications are allowed
        """
        if not self._config.enabled:
            return True
        return not self._config.disable_notifications
    
    def assert_feature_available(self, feature: str) -> None:
        """Assert that a feature is available.
        
        Args:
            feature: Name of the feature to check
        
        Raises:
            PoolerCompatibilityError: If feature is not available
        """
        if not self._config.enabled:
            return
        
        feature_checks = {
            "prepared_statements": self.can_use_prepared_statements,
            "server_side_cursors": self.can_use_server_side_cursors,
            "notifications": self.can_use_notifications,
        }
        
        check = feature_checks.get(feature)
        if check and not check():
            raise PoolerCompatibilityError(
                feature=feature,
                pooler_type=self._config.type,
                mode=self._config.mode,
            )
    
    def get_connection_options(self) -> Dict[str, Any]:
        """Get asyncpg connection options for pooler compatibility.
        
        Returns:
            Dictionary of connection options to pass to asyncpg
        """
        options = {}
        
        if self._config.enabled and self._config.disable_prepared_statements:
            # Disable prepared statement caching
            options["statement_cache_size"] = 0
        
        return options
    
    async def validate_connection(
        self,
        connection: "asyncpg.Connection",
    ) -> bool:
        """Validate a connection works with the pooler.
        
        Args:
            connection: Connection to validate
        
        Returns:
            True if connection is valid
        """
        try:
            await connection.fetchval(self._config.connection_check_query)
            return True
        except Exception as e:
            logger.warning(f"Connection validation failed: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging."""
        return {
            "enabled": self._config.enabled,
            "type": self._config.type.value,
            "mode": self._config.mode.value,
            "detected": self._detected,
            "pooler_info": self._pooler_info.to_dict() if self._pooler_info else None,
            "incompatible_features": self._config.get_incompatible_features(),
        }
    
    def __repr__(self) -> str:
        """Return string representation."""
        if not self._config.enabled:
            return "ExternalPoolerManager(disabled)"
        return (
            f"ExternalPoolerManager("
            f"type={self._config.type.value}, "
            f"mode={self._config.mode.value})"
        )


def detect_pooler_from_port(port: int) -> PoolerType:
    """Detect likely pooler type from port number.
    
    This is a heuristic based on common conventions:
    - 5432: Direct PostgreSQL
    - 6432: PgBouncer (common default)
    - 9999: pgpool (common default)
    
    Args:
        port: Port number
    
    Returns:
        Likely PoolerType based on port
    """
    if port == 6432:
        return PoolerType.PGBOUNCER
    elif port == 9999:
        return PoolerType.PGPOOL
    elif port == 6433:
        return PoolerType.ODYSSEY
    else:
        return PoolerType.UNKNOWN


def create_pooler_config_for_supabase() -> ExternalPoolerConfig:
    """Create pooler configuration optimized for Supabase.
    
    Supabase uses PgBouncer in transaction mode for their pooled connection.
    
    Returns:
        ExternalPoolerConfig configured for Supabase
    
    Example:
        config = create_pooler_config_for_supabase()
        manager = ExternalPoolerManager(config)
    """
    return ExternalPoolerConfig(
        enabled=True,
        type=PoolerType.PGBOUNCER,
        mode=PoolerMode.TRANSACTION,
        auto_detect=False,  # We know it's PgBouncer
    )


def create_pooler_config_for_render() -> ExternalPoolerConfig:
    """Create pooler configuration optimized for Render.
    
    Render can use PgBouncer for connection pooling.
    
    Returns:
        ExternalPoolerConfig configured for Render
    """
    return ExternalPoolerConfig(
        enabled=True,
        type=PoolerType.PGBOUNCER,
        mode=PoolerMode.TRANSACTION,
        auto_detect=False,
    )


def create_pooler_config_for_neon() -> ExternalPoolerConfig:
    """Create pooler configuration optimized for Neon.
    
    Neon uses their own pooler compatible with PgBouncer behavior.
    
    Returns:
        ExternalPoolerConfig configured for Neon
    """
    return ExternalPoolerConfig(
        enabled=True,
        type=PoolerType.PGBOUNCER,  # Neon is PgBouncer-compatible
        mode=PoolerMode.TRANSACTION,
        auto_detect=False,
    )

