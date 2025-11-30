"""
Platform Detection - Auto-Detect Edge Runtime

Automatically detects the deployment platform from
environment variables and file structure.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class EdgePlatform(str, Enum):
    """Supported edge platforms."""
    CLOUDFLARE = "cloudflare"
    VERCEL = "vercel"
    DENO = "deno"
    BUN = "bun"
    UNKNOWN = "unknown"


@dataclass
class PlatformInfo:
    """
    Information about detected platform.
    
    Attributes:
        platform: Detected platform
        version: Platform version if available
        region: Current region
        is_production: Whether in production
    """
    platform: EdgePlatform
    version: Optional[str] = None
    region: Optional[str] = None
    is_production: bool = False
    
    def __bool__(self) -> bool:
        """Check if platform was detected."""
        return self.platform != EdgePlatform.UNKNOWN


def detect_platform() -> PlatformInfo:
    """
    Auto-detect the edge platform.
    
    Checks environment variables and file structure
    to determine the runtime platform.
    
    Returns:
        PlatformInfo with detected platform
        
    Example:
        >>> info = detect_platform()
        >>> if info.platform == EdgePlatform.CLOUDFLARE:
        ...     print("Running on Cloudflare Workers")
    """
    # Check for Cloudflare Workers
    if _is_cloudflare():
        return PlatformInfo(
            platform=EdgePlatform.CLOUDFLARE,
            region=os.environ.get("CF_WORKER_REGION"),
            is_production=os.environ.get("CF_WORKER_ENV") == "production",
        )
    
    # Check for Vercel Edge
    if _is_vercel():
        return PlatformInfo(
            platform=EdgePlatform.VERCEL,
            region=os.environ.get("VERCEL_REGION"),
            is_production=os.environ.get("VERCEL_ENV") == "production",
        )
    
    # Check for Deno Deploy
    if _is_deno():
        return PlatformInfo(
            platform=EdgePlatform.DENO,
            region=os.environ.get("DENO_REGION"),
            is_production=os.environ.get("DENO_DEPLOYMENT_ID") is not None,
        )
    
    # Check for Bun
    if _is_bun():
        return PlatformInfo(
            platform=EdgePlatform.BUN,
            version=os.environ.get("BUN_VERSION"),
        )
    
    return PlatformInfo(platform=EdgePlatform.UNKNOWN)


def _is_cloudflare() -> bool:
    """Check if running on Cloudflare Workers."""
    # Check for CF-specific env vars
    cf_vars = ["CF_PAGES", "CF_WORKER", "CLOUDFLARE_API_TOKEN"]
    if any(os.environ.get(var) for var in cf_vars):
        return True
    
    # Check for wrangler.toml
    if Path("wrangler.toml").exists():
        return True
    
    return False


def _is_vercel() -> bool:
    """Check if running on Vercel Edge."""
    # Check for Vercel env vars
    vercel_vars = ["VERCEL", "VERCEL_URL", "VERCEL_ENV"]
    if any(os.environ.get(var) for var in vercel_vars):
        return True
    
    # Check for vercel.json
    if Path("vercel.json").exists():
        return True
    
    return False


def _is_deno() -> bool:
    """Check if running on Deno Deploy."""
    # Check for Deno env vars
    deno_vars = ["DENO_DEPLOYMENT_ID", "DENO_REGION"]
    if any(os.environ.get(var) for var in deno_vars):
        return True
    
    # Check for deno.json
    if Path("deno.json").exists() or Path("deno.jsonc").exists():
        return True
    
    return False


def _is_bun() -> bool:
    """Check if running on Bun."""
    # Check for Bun env vars
    if os.environ.get("BUN_VERSION"):
        return True
    
    # Check for bunfig.toml
    if Path("bunfig.toml").exists():
        return True
    
    return False


def get_platform_env(platform: EdgePlatform) -> dict:
    """
    Get environment variables for a platform.
    
    Returns platform-specific environment info.
    """
    if platform == EdgePlatform.CLOUDFLARE:
        return {
            "region": os.environ.get("CF_WORKER_REGION"),
            "ray_id": os.environ.get("CF_RAY"),
            "country": os.environ.get("CF_IPCOUNTRY"),
        }
    
    if platform == EdgePlatform.VERCEL:
        return {
            "region": os.environ.get("VERCEL_REGION"),
            "url": os.environ.get("VERCEL_URL"),
            "env": os.environ.get("VERCEL_ENV"),
        }
    
    if platform == EdgePlatform.DENO:
        return {
            "region": os.environ.get("DENO_REGION"),
            "deployment_id": os.environ.get("DENO_DEPLOYMENT_ID"),
        }
    
    if platform == EdgePlatform.BUN:
        return {
            "version": os.environ.get("BUN_VERSION"),
        }
    
    return {}

