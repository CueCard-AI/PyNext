"""
Modal Component for Intercepting Routes.

Provides a modal container that preserves the background page as static
while showing intercepted content in a dialog.

SolidJS Principles Applied:
- Background is static (zero re-render)
- Only modal content hydrates
- URL-driven state (no client state)
- Native dialog element (minimal JS)

Performance Advantages over Next.js:
- Static background (no React tree)
- Minimal modal JS
- Native browser dialog
- No layout shifts
"""

from dataclasses import dataclass
from typing import Optional, Callable, Any, Dict
import uuid
import contextvars

from pynext.core.html import element, div


# Context for modal state
_modal_context: contextvars.ContextVar[Optional["ModalContext"]] = contextvars.ContextVar(
    "modal_context", default=None
)


@dataclass
class ModalContext:
    """Context for modal rendering."""
    is_modal_open: bool = False
    current_path: Optional[str] = None
    background_html: Optional[str] = None
    modal_content: Optional[str] = None


def get_modal_context() -> Optional[ModalContext]:
    """Get current modal context."""
    return _modal_context.get()


def create_modal_context() -> ModalContext:
    """Create a new modal context."""
    ctx = ModalContext()
    _modal_context.set(ctx)
    return ctx


class Modal:
    """
    Modal component for intercepted route content.
    
    Uses the native <dialog> element for accessibility and
    minimal JavaScript overhead.
    
    Args:
        on_close: URL to navigate to when modal closes
        className: CSS class for modal
        overlay_class: CSS class for overlay
        content_class: CSS class for content wrapper
        close_on_overlay: Close when clicking overlay
        close_on_escape: Close when pressing Escape
        show_close_button: Show a close button
        animation: Animation type ("fade", "slide", "scale", "none")
    
    Example:
        Modal(on_close="/")[
            ProductDetails(id=product_id)
        ]
    """
    
    def __init__(
        self,
        on_close: str = "/",
        className: str = "",
        overlay_class: str = "",
        content_class: str = "",
        close_on_overlay: bool = True,
        close_on_escape: bool = True,
        show_close_button: bool = True,
        animation: str = "fade",
    ):
        self.on_close = on_close
        self.className = className
        self.overlay_class = overlay_class
        self.content_class = content_class
        self.close_on_overlay = close_on_overlay
        self.close_on_escape = close_on_escape
        self.show_close_button = show_close_button
        self.animation = animation
        self.id = f"modal-{uuid.uuid4().hex[:8]}"
        self.children: list = []
    
    def __getitem__(self, children: Any) -> "Modal":
        """Add children using bracket syntax."""
        if isinstance(children, tuple):
            self.children = list(children)
        elif isinstance(children, list):
            self.children = children
        else:
            self.children = [children]
        return self
    
    def __call__(self, *children: Any) -> "Modal":
        """Add children using call syntax."""
        self.children = list(children)
        return self
    
    def render(self) -> str:
        """Render the modal."""
        # Render children
        content_parts = []
        for child in self.children:
            if hasattr(child, 'render'):
                content_parts.append(child.render())
            elif callable(child):
                result = child()
                if hasattr(result, 'render'):
                    content_parts.append(result.render())
                else:
                    content_parts.append(str(result))
            else:
                content_parts.append(str(child))
        
        content = "".join(content_parts)
        
        # Build close button
        close_button = ""
        if self.show_close_button:
            close_button = f'''<button
  type="button"
  class="modal-close"
  aria-label="Close"
  data-close-modal
>
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M18 6L6 18M6 6l12 12"/>
  </svg>
</button>'''
        
        # Build modal HTML
        overlay_click = 'data-close-on-overlay="true"' if self.close_on_overlay else ""
        
        return f'''<dialog
  id="{self.id}"
  class="pynext-modal {self.className}"
  data-modal
  data-animation="{self.animation}"
  data-close-url="{self.on_close}"
  {overlay_click}
  open
>
  <div class="modal-backdrop {self.overlay_class}"></div>
  <div class="modal-content {self.content_class}" role="document">
    {close_button}
    {content}
  </div>
</dialog>'''
    
    def get_js_init(self) -> str:
        """Get JavaScript for modal behavior."""
        return f'''
__pynext__.modal.init("{self.id}", {{
  closeUrl: "{self.on_close}",
  closeOnOverlay: {str(self.close_on_overlay).lower()},
  closeOnEscape: {str(self.close_on_escape).lower()},
  animation: "{self.animation}"
}});
'''


class ModalPortal:
    """
    Portal for rendering modal at document root.
    
    This ensures the modal is rendered outside the main content
    flow and at the correct z-index level.
    
    Example:
        # In layout.py
        ModalPortal()  # Add at end of layout
    """
    
    def __init__(self, id: str = "modal-portal"):
        self.id = id
    
    def render(self) -> str:
        """Render the modal portal container."""
        ctx = get_modal_context()
        
        # If there's modal content, render it
        modal_content = ""
        if ctx and ctx.modal_content:
            modal_content = ctx.modal_content
        
        return f'<div id="{self.id}" class="modal-portal">{modal_content}</div>'


# =============================================================================
# Modal JavaScript Runtime
# =============================================================================

def get_modal_runtime_js() -> str:
    """
    Get minimal JavaScript for modal behavior.
    
    Handles:
    - Close on overlay click
    - Close on Escape key
    - Navigation on close
    - Animation in/out
    """
    return """
(function() {
  window.__pynext__ = window.__pynext__ || {};
  window.__pynext__.modal = {
    current: null,
    
    init: function(id, options) {
      var dialog = document.getElementById(id);
      if (!dialog) return;
      
      this.current = { dialog: dialog, options: options };
      
      // Close on backdrop click
      if (options.closeOnOverlay) {
        dialog.querySelector('.modal-backdrop')?.addEventListener('click', function() {
          window.__pynext__.modal.close();
        });
      }
      
      // Close on Escape
      if (options.closeOnEscape) {
        dialog.addEventListener('keydown', function(e) {
          if (e.key === 'Escape') {
            window.__pynext__.modal.close();
          }
        });
      }
      
      // Close button
      dialog.querySelectorAll('[data-close-modal]').forEach(function(btn) {
        btn.addEventListener('click', function() {
          window.__pynext__.modal.close();
        });
      });
      
      // Focus trap
      this.trapFocus(dialog);
      
      // Animate in
      this.animate(dialog, 'in', options.animation);
    },
    
    close: function() {
      if (!this.current) return;
      
      var dialog = this.current.dialog;
      var options = this.current.options;
      
      // Animate out
      this.animate(dialog, 'out', options.animation).then(function() {
        dialog.close();
        
        // Navigate to close URL
        if (options.closeUrl && window.__pynext__.navigate) {
          window.__pynext__.navigate(options.closeUrl, { replace: true });
        } else if (options.closeUrl) {
          window.history.back();
        }
      });
      
      this.current = null;
    },
    
    animate: function(dialog, direction, type) {
      return new Promise(function(resolve) {
        if (type === 'none') {
          resolve();
          return;
        }
        
        var content = dialog.querySelector('.modal-content');
        var backdrop = dialog.querySelector('.modal-backdrop');
        
        var animations = {
          fade: {
            in: [{ opacity: 0 }, { opacity: 1 }],
            out: [{ opacity: 1 }, { opacity: 0 }]
          },
          scale: {
            in: [{ opacity: 0, transform: 'scale(0.95)' }, { opacity: 1, transform: 'scale(1)' }],
            out: [{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(0.95)' }]
          },
          slide: {
            in: [{ opacity: 0, transform: 'translateY(20px)' }, { opacity: 1, transform: 'translateY(0)' }],
            out: [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: 'translateY(20px)' }]
          }
        };
        
        var keyframes = animations[type] || animations.fade;
        
        content?.animate(keyframes[direction], {
          duration: 200,
          easing: 'ease-out',
          fill: 'forwards'
        });
        
        backdrop?.animate(keyframes.fade[direction], {
          duration: 200,
          easing: 'ease-out',
          fill: 'forwards'
        }).onfinish = resolve;
      });
    },
    
    trapFocus: function(dialog) {
      var focusables = dialog.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      var first = focusables[0];
      var last = focusables[focusables.length - 1];
      
      if (first) first.focus();
      
      dialog.addEventListener('keydown', function(e) {
        if (e.key !== 'Tab') return;
        
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      });
    }
  };
})();
"""


# =============================================================================
# Modal CSS
# =============================================================================

def get_modal_css() -> str:
    """Get CSS for modal styling."""
    return """
.pynext-modal {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  padding: 0;
  margin: 0;
  border: none;
  background: transparent;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pynext-modal::backdrop {
  display: none;
}

.modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  max-width: 90vw;
  max-height: 90vh;
  overflow: auto;
  z-index: 1;
}

.modal-close {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  color: #6b7280;
  transition: color 0.2s, background-color 0.2s;
  z-index: 10;
}

.modal-close:hover {
  color: #1f2937;
  background: #f3f4f6;
}

.modal-close:focus {
  outline: none;
  box-shadow: 0 0 0 2px #3b82f6;
}

/* Animation styles */
.pynext-modal[data-animation="fade"] .modal-content,
.pynext-modal[data-animation="fade"] .modal-backdrop {
  animation: modal-fade-in 0.2s ease-out;
}

.pynext-modal[data-animation="scale"] .modal-content {
  animation: modal-scale-in 0.2s ease-out;
}

.pynext-modal[data-animation="slide"] .modal-content {
  animation: modal-slide-in 0.2s ease-out;
}

@keyframes modal-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes modal-scale-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes modal-slide-in {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Responsive */
@media (max-width: 640px) {
  .modal-content {
    max-width: 100%;
    max-height: 100%;
    border-radius: 0;
    margin: 0;
  }
  
  .pynext-modal[data-animation="slide"] .modal-content {
    animation: modal-slide-up 0.3s ease-out;
  }
  
  @keyframes modal-slide-up {
    from { transform: translateY(100%); }
    to { transform: translateY(0); }
  }
}
"""


# =============================================================================
# Modal Helper Functions
# =============================================================================

def modal(
    on_close: str = "/",
    **props
) -> Modal:
    """Create a modal with sensible defaults."""
    return Modal(on_close=on_close, **props)


def photo_modal(on_close: str = "/") -> Modal:
    """Photo-optimized modal (larger, dark backdrop)."""
    return Modal(
        on_close=on_close,
        overlay_class="photo-modal-overlay",
        content_class="photo-modal-content",
        animation="fade",
    )


def form_modal(on_close: str = "/") -> Modal:
    """Form-optimized modal (medium size, prevents accidental close)."""
    return Modal(
        on_close=on_close,
        close_on_overlay=False,
        animation="scale",
    )


def needs_modal_runtime() -> bool:
    """Check if current page needs modal runtime."""
    ctx = get_modal_context()
    return ctx is not None and ctx.is_modal_open

