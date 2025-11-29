"""
Robots.txt Generation for PyNext.

Configure which pages search engines can crawl.

Example:
    from pynext import RobotsConfig, RobotsRule
    
    robots = RobotsConfig(
        rules=[
            RobotsRule(user_agent="*", allow=["/"], disallow=["/admin"]),
        ],
        sitemap=True,
    )

Why This Matters:
    Robots.txt tells search engines which pages to crawl (or not).
    It protects private pages and prevents crawler overload.
    PyNext makes it simple with Python configuration.

SolidJS Principles:
    - Explicit: Clear rules for each bot
    - Minimal: One-liner shortcuts for common cases
    - Compile-time: Generated at build, not runtime
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ============================================
# Data Classes
# ============================================

@dataclass
class RobotsRule:
    """
    A single rule in robots.txt.
    
    Each rule applies to a specific user agent (crawler).
    
    Attributes:
        user_agent: Which crawler this rule applies to ("*" = all)
        allow: Paths the crawler CAN access
        disallow: Paths the crawler CANNOT access
        crawl_delay: Seconds between requests (optional)
    
    Example:
        # Allow all paths except /admin
        rule = RobotsRule(
            user_agent="*",
            allow=["/"],
            disallow=["/admin", "/api"],
        )
        
        # Rate-limit Googlebot
        rule = RobotsRule(
            user_agent="Googlebot",
            crawl_delay=1,
        )
    """
    user_agent: str = "*"
    allow: List[str] = field(default_factory=list)
    disallow: List[str] = field(default_factory=list)
    crawl_delay: Optional[int] = None
    
    def __post_init__(self):
        """Validate rule fields."""
        if not self.user_agent:
            raise ValueError("user_agent is required")
        
        if self.crawl_delay is not None and self.crawl_delay < 0:
            raise ValueError(f"crawl_delay must be >= 0, got: {self.crawl_delay}")
    
    def to_text(self) -> str:
        """
        Convert to robots.txt format.
        
        Returns:
            Text block for this rule
        """
        lines = [f"User-agent: {self.user_agent}"]
        
        for path in self.allow:
            lines.append(f"Allow: {path}")
        
        for path in self.disallow:
            lines.append(f"Disallow: {path}")
        
        if self.crawl_delay is not None:
            lines.append(f"Crawl-delay: {self.crawl_delay}")
        
        return "\n".join(lines)


@dataclass
class RobotsConfig:
    """
    Complete robots.txt configuration.
    
    Defines all rules and settings for robots.txt generation.
    
    Attributes:
        rules: List of RobotsRule objects
        sitemap: Whether to include sitemap URL
        sitemap_url: Override sitemap URL (auto-detected if None)
        host: Preferred host (optional, for non-www redirect hint)
    
    Example:
        config = RobotsConfig(
            rules=[
                RobotsRule(user_agent="*", allow=["/"], disallow=["/admin"]),
                RobotsRule(user_agent="Googlebot", crawl_delay=1),
            ],
            sitemap=True,
        )
        
        text = config.generate("https://example.com")
        print(text)
    """
    rules: List[RobotsRule] = field(default_factory=list)
    sitemap: bool = True
    sitemap_url: Optional[str] = None
    host: Optional[str] = None
    
    def __post_init__(self):
        """Set default rule if none provided."""
        # If no rules, default to allow all
        if not self.rules:
            self.rules = [RobotsRule(user_agent="*", allow=["/"])]
    
    def generate(self, base_url: str) -> str:
        """
        Generate robots.txt content.
        
        Args:
            base_url: Base URL for sitemap reference
        
        Returns:
            Complete robots.txt content
        """
        base_url = base_url.rstrip("/")
        lines = []
        
        # Add rules
        for i, rule in enumerate(self.rules):
            if i > 0:
                lines.append("")  # Blank line between rules
            lines.append(rule.to_text())
        
        # Add sitemap
        if self.sitemap:
            lines.append("")
            sitemap_url = self.sitemap_url or f"{base_url}/sitemap.xml"
            lines.append(f"Sitemap: {sitemap_url}")
        
        # Add host hint (optional)
        if self.host:
            lines.append("")
            lines.append(f"Host: {self.host}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "rules": [
                {
                    "user_agent": r.user_agent,
                    "allow": r.allow,
                    "disallow": r.disallow,
                    "crawl_delay": r.crawl_delay,
                }
                for r in self.rules
            ],
            "sitemap": self.sitemap,
            "sitemap_url": self.sitemap_url,
            "host": self.host,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RobotsConfig":
        """Create from dictionary."""
        rules = [
            RobotsRule(
                user_agent=r.get("user_agent", "*"),
                allow=r.get("allow", []),
                disallow=r.get("disallow", []),
                crawl_delay=r.get("crawl_delay"),
            )
            for r in data.get("rules", [])
        ]
        
        return cls(
            rules=rules,
            sitemap=data.get("sitemap", True),
            sitemap_url=data.get("sitemap_url"),
            host=data.get("host"),
        )


# ============================================
# Convenience Functions
# ============================================

def robots_allow_all(
    except_paths: Optional[List[str]] = None,
    sitemap: bool = True,
) -> RobotsConfig:
    """
    Create robots.txt that allows all crawlers.
    
    Simple one-liner for open sites.
    
    Args:
        except_paths: Paths to disallow (e.g., ["/admin", "/api"])
        sitemap: Include sitemap URL
    
    Returns:
        RobotsConfig that allows everything
    
    Example:
        # Allow everything
        robots = robots_allow_all()
        
        # Allow everything except admin
        robots = robots_allow_all(except_paths=["/admin", "/api"])
    """
    disallow = except_paths or []
    
    return RobotsConfig(
        rules=[
            RobotsRule(
                user_agent="*",
                allow=["/"],
                disallow=disallow,
            )
        ],
        sitemap=sitemap,
    )


def robots_disallow_all(sitemap: bool = False) -> RobotsConfig:
    """
    Create robots.txt that blocks all crawlers.
    
    Use for staging/development sites.
    
    Args:
        sitemap: Include sitemap URL (default False)
    
    Returns:
        RobotsConfig that blocks everything
    
    Example:
        # Block all crawlers
        robots = robots_disallow_all()
    """
    return RobotsConfig(
        rules=[
            RobotsRule(
                user_agent="*",
                disallow=["/"],
            )
        ],
        sitemap=sitemap,
    )


def robots_from_paths(
    allow: Optional[List[str]] = None,
    disallow: Optional[List[str]] = None,
    sitemap: bool = True,
) -> RobotsConfig:
    """
    Create robots.txt from allow/disallow lists.
    
    Simple way to configure basic rules.
    
    Args:
        allow: Paths to allow
        disallow: Paths to disallow
        sitemap: Include sitemap URL
    
    Returns:
        RobotsConfig with specified rules
    
    Example:
        robots = robots_from_paths(
            allow=["/", "/products"],
            disallow=["/admin", "/api", "/internal"],
        )
    """
    return RobotsConfig(
        rules=[
            RobotsRule(
                user_agent="*",
                allow=allow or [],
                disallow=disallow or [],
            )
        ],
        sitemap=sitemap,
    )


# ============================================
# Robots Generator
# ============================================

class RobotsGenerator:
    """
    Generates robots.txt from configuration.
    
    Supports both static config and dynamic generation.
    
    Example:
        from pynext.seo import RobotsGenerator, RobotsConfig
        
        config = RobotsConfig(
            rules=[RobotsRule(user_agent="*", allow=["/"])],
            sitemap=True,
        )
        
        generator = RobotsGenerator(config, "https://example.com")
        text = generator.generate()
    """
    
    def __init__(self, config: RobotsConfig, base_url: str):
        """
        Initialize generator.
        
        Args:
            config: RobotsConfig with rules
            base_url: Base URL for sitemap reference
        """
        self.config = config
        self.base_url = base_url.rstrip("/")
    
    def generate(self) -> str:
        """
        Generate robots.txt content.
        
        Returns:
            Complete robots.txt string
        """
        return self.config.generate(self.base_url)
    
    def write_to_file(self, output_path: Path) -> Path:
        """
        Write robots.txt to file.
        
        Args:
            output_path: Path to write file
        
        Returns:
            Path to written file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.generate(), encoding="utf-8")
        return output_path
    
    def validate(self) -> List[str]:
        """
        Validate the robots.txt configuration.
        
        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []
        
        # Check for conflicting rules
        for rule in self.config.rules:
            for allow_path in rule.allow:
                if allow_path in rule.disallow:
                    warnings.append(
                        f"Path '{allow_path}' is both allowed and disallowed "
                        f"for user-agent '{rule.user_agent}'"
                    )
        
        # Check for empty rules
        for rule in self.config.rules:
            if not rule.allow and not rule.disallow and rule.crawl_delay is None:
                warnings.append(
                    f"Rule for '{rule.user_agent}' has no allow, disallow, or crawl-delay"
                )
        
        # Check sitemap URL format
        if self.config.sitemap_url:
            if not self.config.sitemap_url.startswith(("http://", "https://")):
                warnings.append(
                    f"Sitemap URL should be absolute: {self.config.sitemap_url}"
                )
        
        return warnings

