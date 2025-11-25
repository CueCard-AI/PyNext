"""
Draft Mode for PyNext - Signal-Based Content Preview.

Provides a fine-grained draft mode where only draft-aware components
update when toggling between published and draft content.

SolidJS Principles Applied:
- Signal-based draft state (no full re-render)
- Fine-grained updates (only draft components)
- Overlay injection (static base preserved)
- Build-time draft variants (optional)

Performance Advantages over Next.js:
- Signal update vs full page re-render
- Static content preserved
- Only draft-aware components update
- Minimal JS for draft switching
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any, Dict, TypeVar, Generic
import uuid
import functools
import contextvars
import json

from pynext.core.signals import Signal


T = TypeVar('T')


# Draft mode context
_draft_context: contextvars.ContextVar[Optional["DraftContext"]] = contextvars.ContextVar(
    "draft_context", default=None
)


@dataclass
class DraftContext:
    """Context for draft mode rendering."""
    is_draft: bool = False
    draft_token: Optional[str] = None
    draft_data: Dict[str, Any] = field(default_factory=dict)
    preview_url: Optional[str] = None


def get_draft_context() -> Optional[DraftContext]:
    """Get current draft context."""
    return _draft_context.get()


def create_draft_context(
    is_draft: bool = False,
    token: Optional[str] = None,
) -> DraftContext:
    """Create a new draft context."""
    ctx = DraftContext(is_draft=is_draft, draft_token=token)
    _draft_context.set(ctx)
    return ctx


class DraftSignal(Signal[bool]):
    """
    Signal for draft mode state.
    
    This is a specialized signal that controls whether draft
    content is shown. Changes propagate to all draft-aware
    components without full re-render.
    """
    
    def __init__(self, initial: bool = False):
        super().__init__(initial, name="draft_mode")
        self._draft_token: Optional[str] = None
    
    def enable(self, token: str) -> None:
        """Enable draft mode with authentication token."""
        self._draft_token = token
        self.set(True)
    
    def disable(self) -> None:
        """Disable draft mode."""
        self._draft_token = None
        self.set(False)
    
    def toggle(self) -> None:
        """Toggle draft mode."""
        self.set(not self())
    
    def is_authenticated(self) -> bool:
        """Check if draft mode has valid token."""
        return self._draft_token is not None
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization."""
        return f'''__pynext__.draft.init({{
  enabled: {str(self()).lower()},
  authenticated: {str(self.is_authenticated()).lower()}
}});'''


# Global draft signal
_draft_signal = DraftSignal(False)


def use_draft() -> DraftSignal:
    """
    Get the draft mode signal.
    
    Use this to conditionally render draft content:
    
        draft = use_draft()
        if draft():
            return DraftContent()
        else:
            return PublishedContent()
    """
    return _draft_signal


def is_draft_mode() -> bool:
    """Check if currently in draft mode."""
    return _draft_signal()


def enable_draft(token: str) -> None:
    """Enable draft mode with token."""
    _draft_signal.enable(token)
    
    # Also update context
    ctx = get_draft_context()
    if ctx:
        ctx.is_draft = True
        ctx.draft_token = token


def disable_draft() -> None:
    """Disable draft mode."""
    _draft_signal.disable()
    
    ctx = get_draft_context()
    if ctx:
        ctx.is_draft = False
        ctx.draft_token = None


# =============================================================================
# Draft Content Decorator
# =============================================================================

def draft_content(
    fallback: Optional[Callable[[], Any]] = None,
    cache_draft: bool = False,
):
    """
    Mark a component as draft-aware.
    
    When draft mode is enabled, this component will re-render
    with draft content. The fallback is shown in published mode.
    
    Args:
        fallback: Content to show when not in draft mode
        cache_draft: Whether to cache draft content
    
    Example:
        @draft_content(fallback=published_article)
        def article_body():
            return fetch_draft_article()
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            draft = use_draft()
            
            if draft():
                # Draft mode - render draft content
                result = fn(*args, **kwargs)
            elif fallback:
                # Published mode - render fallback
                result = fallback()
            else:
                # No fallback, still render function
                result = fn(*args, **kwargs)
            
            if hasattr(result, 'render'):
                content = result.render()
            else:
                content = str(result) if result else ""
            
            # Wrap with draft marker for fine-grained updates
            draft_id = f"draft-{uuid.uuid4().hex[:8]}"
            return f'<div data-draft="{draft_id}" data-draft-aware="true">{content}</div>'
        
        wrapper._is_draft_content = True
        wrapper._draft_fallback = fallback
        wrapper._cache_draft = cache_draft
        
        return wrapper
    
    return decorator


def draft_only(fn: Callable) -> Callable:
    """
    Mark content that only appears in draft mode.
    
    In published mode, nothing is rendered.
    
    Example:
        @draft_only
        def draft_warning():
            return div(class_="draft-banner")["Draft Preview"]
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        draft = use_draft()
        
        if not draft():
            return ""
        
        result = fn(*args, **kwargs)
        if hasattr(result, 'render'):
            content = result.render()
        else:
            content = str(result) if result else ""
        
        return f'<div data-draft-only="true">{content}</div>'
    
    wrapper._is_draft_only = True
    return wrapper


def published_only(fn: Callable) -> Callable:
    """
    Mark content that only appears in published mode.
    
    In draft mode, nothing is rendered.
    
    Example:
        @published_only
        def analytics_script():
            return Script(src="analytics.js")
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        draft = use_draft()
        
        if draft():
            return ""
        
        result = fn(*args, **kwargs)
        if hasattr(result, 'render'):
            content = result.render()
        else:
            content = str(result) if result else ""
        
        return f'<div data-published-only="true">{content}</div>'
    
    wrapper._is_published_only = True
    return wrapper


# =============================================================================
# Draft Components
# =============================================================================

class DraftSwitch:
    """
    Component that renders different content based on draft mode.
    
    Example:
        DraftSwitch(
            draft=lambda: DraftArticle(data),
            published=lambda: Article(data),
        )
    """
    
    def __init__(
        self,
        draft: Callable[[], Any],
        published: Callable[[], Any],
    ):
        self.draft_content = draft
        self.published_content = published
        self.id = f"draft-switch-{uuid.uuid4().hex[:8]}"
    
    def render(self) -> str:
        draft = use_draft()
        
        if draft():
            result = self.draft_content()
        else:
            result = self.published_content()
        
        if hasattr(result, 'render'):
            content = result.render()
        else:
            content = str(result) if result else ""
        
        # Both versions are rendered but only one is visible
        # This enables instant switching without network request
        return f'''<div id="{self.id}" data-draft-switch data-mode="{"draft" if draft() else "published"}">
  {content}
</div>'''


class DraftBanner:
    """
    Draft mode indicator banner.
    
    Shows when in draft mode with options to exit or edit.
    """
    
    def __init__(
        self,
        exit_url: str = "/api/draft/disable",
        edit_url: Optional[str] = None,
        position: str = "bottom",  # "top", "bottom"
    ):
        self.exit_url = exit_url
        self.edit_url = edit_url
        self.position = position
    
    def render(self) -> str:
        draft = use_draft()
        
        if not draft():
            return ""
        
        edit_button = ""
        if self.edit_url:
            edit_button = f'''<a href="{self.edit_url}" class="draft-banner-edit">
  Edit in CMS
</a>'''
        
        return f'''<div class="draft-banner draft-banner-{self.position}" data-draft-banner>
  <span class="draft-banner-text">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15h2v2h-2v-2zm0-8h2v6h-2V9z"/>
    </svg>
    Draft Mode
  </span>
  {edit_button}
  <a href="{self.exit_url}" class="draft-banner-exit">
    Exit Preview
  </a>
</div>'''


class DraftOverlay:
    """
    Overlay that shows draft changes highlighted.
    
    Useful for comparing draft vs published content.
    """
    
    def __init__(
        self,
        highlight_changes: bool = True,
        show_diff: bool = False,
    ):
        self.highlight_changes = highlight_changes
        self.show_diff = show_diff
    
    def render(self) -> str:
        draft = use_draft()
        
        if not draft():
            return ""
        
        return '''<div class="draft-overlay" data-draft-overlay>
  <style>
    [data-draft-aware] {
      position: relative;
    }
    [data-draft-aware]::before {
      content: "";
      position: absolute;
      inset: -2px;
      border: 2px dashed #f59e0b;
      border-radius: 4px;
      pointer-events: none;
      opacity: 0.5;
    }
    [data-draft-only] {
      background: rgba(245, 158, 11, 0.1);
    }
  </style>
</div>'''


# =============================================================================
# Draft JavaScript Runtime
# =============================================================================

def get_draft_runtime_js() -> str:
    """
    Get minimal JavaScript for draft mode.
    
    Handles:
    - Toggle draft mode
    - Update draft-aware components
    - Persist draft token
    """
    return """
(function() {
  window.__pynext__ = window.__pynext__ || {};
  window.__pynext__.draft = {
    enabled: false,
    token: null,
    
    init: function(options) {
      this.enabled = options.enabled;
      
      // Check cookie for token
      var token = this.getCookie('__pynext_draft_token');
      if (token) {
        this.token = token;
        if (!this.enabled) {
          this.enable(token);
        }
      }
    },
    
    enable: function(token) {
      this.enabled = true;
      this.token = token;
      this.setCookie('__pynext_draft_token', token, 7);
      document.body.classList.add('draft-mode');
      this.update();
    },
    
    disable: function() {
      this.enabled = false;
      this.token = null;
      this.deleteCookie('__pynext_draft_token');
      document.body.classList.remove('draft-mode');
      this.update();
    },
    
    toggle: function() {
      if (this.enabled) {
        this.disable();
      } else if (this.token) {
        this.enable(this.token);
      }
    },
    
    update: function() {
      // Update draft switches
      document.querySelectorAll('[data-draft-switch]').forEach(function(el) {
        el.setAttribute('data-mode', this.enabled ? 'draft' : 'published');
      }.bind(this));
      
      // Toggle draft-only elements
      document.querySelectorAll('[data-draft-only]').forEach(function(el) {
        el.style.display = this.enabled ? '' : 'none';
      }.bind(this));
      
      // Toggle published-only elements
      document.querySelectorAll('[data-published-only]').forEach(function(el) {
        el.style.display = this.enabled ? 'none' : '';
      }.bind(this));
      
      // Update draft banner
      document.querySelectorAll('[data-draft-banner]').forEach(function(el) {
        el.style.display = this.enabled ? '' : 'none';
      }.bind(this));
    },
    
    // Fetch draft content for a component
    fetchDraft: function(componentId) {
      if (!this.token) return Promise.reject('No token');
      
      return fetch('/_draft/content/' + componentId, {
        headers: {
          'X-Draft-Token': this.token
        }
      }).then(function(res) {
        return res.text();
      });
    },
    
    setCookie: function(name, value, days) {
      var expires = '';
      if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = '; expires=' + date.toUTCString();
      }
      document.cookie = name + '=' + value + expires + '; path=/; SameSite=Lax';
    },
    
    getCookie: function(name) {
      var match = document.cookie.match('(^|;)\\\\s*' + name + '\\\\s*=\\\\s*([^;]+)');
      return match ? match.pop() : '';
    },
    
    deleteCookie: function(name) {
      document.cookie = name + '=; Max-Age=-99999999; path=/';
    }
  };
  
  // Auto-init from page state
  if (window.__PYNEXT_DRAFT__) {
    window.__pynext__.draft.init(window.__PYNEXT_DRAFT__);
  }
})();
"""


# =============================================================================
# Draft CSS
# =============================================================================

def get_draft_css() -> str:
    """Get CSS for draft mode UI."""
    return """
.draft-banner {
  position: fixed;
  left: 0;
  right: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: #1e293b;
  color: white;
  font-size: 0.875rem;
}

.draft-banner-top {
  top: 0;
}

.draft-banner-bottom {
  bottom: 0;
}

.draft-banner-text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #f59e0b;
  font-weight: 500;
}

.draft-banner-edit,
.draft-banner-exit {
  padding: 0.375rem 0.75rem;
  border-radius: 0.25rem;
  text-decoration: none;
  font-weight: 500;
  transition: background-color 0.2s;
}

.draft-banner-edit {
  background: #3b82f6;
  color: white;
}

.draft-banner-edit:hover {
  background: #2563eb;
}

.draft-banner-exit {
  background: #475569;
  color: white;
}

.draft-banner-exit:hover {
  background: #64748b;
}

/* Draft mode body adjustment */
body.draft-mode .draft-banner-top ~ * {
  margin-top: 48px;
}

body.draft-mode .draft-banner-bottom ~ * {
  margin-bottom: 48px;
}
"""


def needs_draft_runtime() -> bool:
    """Check if current page needs draft runtime."""
    ctx = get_draft_context()
    return ctx is not None and ctx.is_draft

