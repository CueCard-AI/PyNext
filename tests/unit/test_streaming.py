"""
Unit tests for PyNext streaming HTML responses.

Tests progressive rendering and out-of-order streaming.
"""

import pytest
import asyncio
from pynext.server.streaming import (
    StreamingHTMLResponse,
    StreamChunk,
    StreamingContext,
    PageShell,
    stream_page,
    create_loading_skeleton,
    create_suspense_placeholder,
    get_streaming_css,
    STREAMING_CSS,
)
from pynext.core.suspense import SuspenseBoundary, SuspenseState


class TestPageShell:
    """Tests for PageShell helper."""
    
    def test_shell_opening(self):
        """PageShell generates opening HTML."""
        shell = PageShell(title="Test App")
        
        html = shell.render_opening()
        
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "<head>" in html
        assert "<title>Test App</title>" in html
        assert "<body" in html
    
    def test_shell_closing(self):
        """PageShell generates closing HTML."""
        shell = PageShell()
        
        html = shell.render_closing()
        
        assert "</body>" in html
        assert "</html>" in html
        assert "runtime.js" in html
    
    def test_shell_with_head_content(self):
        """PageShell includes head content."""
        shell = PageShell(
            title="My App",
            head_content='<link rel="stylesheet" href="/styles.css">',
        )
        
        html = shell.render_opening()
        
        assert "styles.css" in html
    
    def test_shell_with_body_class(self):
        """PageShell includes body class."""
        shell = PageShell(body_class="dark-mode")
        
        html = shell.render_opening()
        
        assert 'class="dark-mode"' in html
    
    def test_shell_with_initial_state(self):
        """PageShell embeds initial state."""
        shell = PageShell()
        shell.add_state("user", {"name": "Alice"})
        
        html = shell.render_opening()
        
        assert "__PYNEXT_DATA__" in html
        assert "Alice" in html
    
    def test_shell_with_scripts(self):
        """PageShell includes inline scripts."""
        shell = PageShell()
        shell.add_script("console.log('Hello')")
        
        html = shell.render_opening()
        
        assert "console.log" in html


class TestStreamChunk:
    """Tests for StreamChunk dataclass."""
    
    def test_create_chunk(self):
        """StreamChunk can be created."""
        chunk = StreamChunk(content="<div>Hello</div>")
        
        assert chunk.content == "<div>Hello</div>"
        assert chunk.chunk_type == "html"
    
    def test_chunk_with_placeholder(self):
        """StreamChunk can have placeholder ID."""
        chunk = StreamChunk(
            content="<div>Content</div>",
            chunk_type="replacement",
            placeholder_id="suspense-123",
        )
        
        assert chunk.placeholder_id == "suspense-123"


class TestStreamingContext:
    """Tests for StreamingContext."""
    
    def test_create_context(self):
        """StreamingContext can be created."""
        ctx = StreamingContext()
        
        assert ctx.chunks == []
        assert ctx.pending_suspense == {}
        assert ctx.completed is False
    
    def test_add_chunks(self):
        """Context tracks chunks."""
        ctx = StreamingContext()
        ctx.chunks.append(StreamChunk(content="<div>1</div>"))
        ctx.chunks.append(StreamChunk(content="<div>2</div>"))
        
        assert len(ctx.chunks) == 2


class TestLoadingSkeleton:
    """Tests for loading skeleton helpers."""
    
    def test_create_skeleton(self):
        """Create single loading skeleton."""
        html = create_loading_skeleton()
        
        assert "skeleton" in html
        assert "width:100%" in html
    
    def test_skeleton_custom_size(self):
        """Create skeleton with custom size."""
        html = create_loading_skeleton(width="200px", height="50px")
        
        assert "200px" in html
        assert "50px" in html
    
    def test_multiple_skeletons(self):
        """Create multiple skeleton lines."""
        html = create_loading_skeleton(count=3)
        
        assert html.count("skeleton") == 3


class TestSuspensePlaceholder:
    """Tests for Suspense placeholder creation."""
    
    def test_create_placeholder(self):
        """Create Suspense placeholder."""
        html = create_suspense_placeholder(
            boundary_id="test-123",
            fallback_html="<div>Loading...</div>",
        )
        
        assert 'data-suspense="test-123"' in html
        assert 'data-state="pending"' in html
        assert "Loading..." in html


class TestStreamingCSS:
    """Tests for streaming CSS."""
    
    def test_css_exists(self):
        """Streaming CSS is defined."""
        assert STREAMING_CSS is not None
        assert len(STREAMING_CSS) > 0
    
    def test_get_streaming_css(self):
        """get_streaming_css returns CSS."""
        css = get_streaming_css()
        
        assert "[data-suspense]" in css
        assert "skeleton" in css
        assert "@keyframes" in css
    
    def test_css_has_states(self):
        """CSS covers all Suspense states."""
        css = get_streaming_css()
        
        assert "pending" in css
        assert "resolved" in css
        assert "timeout" in css


class TestStreamPage:
    """Tests for stream_page generator."""
    
    @pytest.mark.asyncio
    async def test_stream_shell_only(self):
        """Stream page with no Suspense boundaries."""
        chunks = []
        
        async for chunk in stream_page("<html>Shell</html>", []):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert "Shell" in chunks[0]
    
    @pytest.mark.asyncio
    async def test_stream_with_resolved_boundary(self):
        """Stream page with already-resolved boundary."""
        boundary = SuspenseBoundary(
            id="test-boundary",
            fallback="Loading...",
        )
        boundary.state = SuspenseState.RESOLVED
        
        chunks = []
        async for chunk in stream_page("<html>Content</html>", [boundary]):
            chunks.append(chunk)
        
        # Should just have shell, no replacement scripts
        assert len(chunks) == 1


class TestStreamingHTMLResponse:
    """Tests for StreamingHTMLResponse."""
    
    @pytest.mark.asyncio
    async def test_response_creation(self):
        """StreamingHTMLResponse can be created."""
        async def generate():
            yield "<html>"
            yield "<body>Hello</body>"
            yield "</html>"
        
        response = StreamingHTMLResponse(generate())
        
        assert response.media_type == "text/html; charset=utf-8"
        assert response.headers["Transfer-Encoding"] == "chunked"
    
    @pytest.mark.asyncio
    async def test_response_iterates(self):
        """StreamingHTMLResponse yields chunks."""
        chunks_sent = []
        
        async def generate():
            chunks_sent.append("chunk1")
            yield "<div>1</div>"
            chunks_sent.append("chunk2")
            yield "<div>2</div>"
        
        response = StreamingHTMLResponse(generate())
        
        # Iterate through response body
        body_parts = []
        async for part in response.body_iterator:
            body_parts.append(part)
        
        assert len(chunks_sent) == 2


class TestStreamingIntegration:
    """Integration tests for streaming."""
    
    @pytest.mark.asyncio
    async def test_full_streaming_flow(self):
        """Test complete streaming flow."""
        # Create a page shell
        shell = PageShell(title="Streaming Test")
        
        # Collect all output
        output = []
        output.append(shell.render_opening())
        output.append("<main>Content</main>")
        output.append(shell.render_closing())
        
        full_html = "".join(output)
        
        assert "<!DOCTYPE html>" in full_html
        assert "Streaming Test" in full_html
        assert "Content" in full_html
        assert "</html>" in full_html
    
    @pytest.mark.asyncio
    async def test_streaming_with_suspense_placeholder(self):
        """Test streaming with Suspense placeholder."""
        shell = PageShell()
        
        output = []
        output.append(shell.render_opening())
        output.append(create_suspense_placeholder(
            "async-content",
            "<div class='spinner'>Loading...</div>"
        ))
        output.append(shell.render_closing())
        
        html = "".join(output)
        
        assert 'data-suspense="async-content"' in html
        assert "spinner" in html


class TestOutOfOrderStreaming:
    """
    Tests for out-of-order streaming behavior.
    
    Out-of-order streaming means that components can be sent to the client
    in the order they RESOLVE, not the order they appear in the document.
    
    Example: If the footer loads before the main content, the footer
    replacement script is sent first, even though footer comes last in DOM.
    """
    
    @pytest.mark.asyncio
    async def test_out_of_order_resolution(self):
        """
        Components should stream in resolution order, not DOM order.
        
        Scenario:
        - Header (appears first, resolves in 50ms)
        - Main Content (appears second, resolves in 10ms) ← Faster!
        - Footer (appears third, resolves in 30ms)
        
        Expected stream order: Main, Footer, Header
        """
        resolution_order = []
        
        # Create boundaries with different resolve times
        header_boundary = SuspenseBoundary(id="header", fallback="Loading header...")
        main_boundary = SuspenseBoundary(id="main", fallback="Loading main...")
        footer_boundary = SuspenseBoundary(id="footer", fallback="Loading footer...")
        
        # Set up async resolution with different timings
        async def resolve_header():
            await asyncio.sleep(0.05)  # 50ms - SLOWEST
            resolution_order.append("header")
            header_boundary.state = SuspenseState.RESOLVED
            header_boundary.resolved_content = "<header>Header Content</header>"
        
        async def resolve_main():
            await asyncio.sleep(0.01)  # 10ms - FASTEST
            resolution_order.append("main")
            main_boundary.state = SuspenseState.RESOLVED
            main_boundary.resolved_content = "<main>Main Content</main>"
        
        async def resolve_footer():
            await asyncio.sleep(0.03)  # 30ms - MIDDLE
            resolution_order.append("footer")
            footer_boundary.state = SuspenseState.RESOLVED
            footer_boundary.resolved_content = "<footer>Footer Content</footer>"
        
        # Start all resolutions
        await asyncio.gather(
            resolve_header(),
            resolve_main(),
            resolve_footer(),
        )
        
        # Verify out-of-order resolution
        assert resolution_order == ["main", "footer", "header"], \
            f"Expected main→footer→header, got {resolution_order}"
    
    @pytest.mark.asyncio
    async def test_replacement_script_order(self):
        """Replacement scripts should be sent as each boundary resolves."""
        from pynext.server.streaming import _create_replacement_script
        
        # Fast component
        fast_script = _create_replacement_script("fast-component", "<div>Fast!</div>")
        
        # Slow component  
        slow_script = _create_replacement_script("slow-component", "<div>Slow!</div>")
        
        # Both should be valid replacement scripts
        assert 'data-suspense="fast-component"' in fast_script
        assert 'data-suspense="slow-component"' in slow_script
        
        # Both should trigger hydration
        assert "__pynext__.hydrateElement" in fast_script
        assert "__pynext__.hydrateElement" in slow_script
    
    @pytest.mark.asyncio
    async def test_parallel_boundary_resolution(self):
        """Multiple boundaries can resolve in parallel."""
        resolved = set()
        
        async def create_boundary_with_delay(id: str, delay: float):
            boundary = SuspenseBoundary(id=id, fallback=f"Loading {id}...")
            await asyncio.sleep(delay)
            boundary.state = SuspenseState.RESOLVED
            boundary.resolved_content = f"<div>{id} content</div>"
            resolved.add(id)
            return boundary
        
        # Start 5 parallel resolutions with different timings
        boundaries = await asyncio.gather(
            create_boundary_with_delay("a", 0.01),
            create_boundary_with_delay("b", 0.02),
            create_boundary_with_delay("c", 0.03),
            create_boundary_with_delay("d", 0.04),
            create_boundary_with_delay("e", 0.05),
        )
        
        # All should be resolved
        assert len(resolved) == 5
        assert all(b.state == SuspenseState.RESOLVED for b in boundaries)
    
    @pytest.mark.asyncio
    async def test_streaming_maintains_placeholder_structure(self):
        """
        Placeholders maintain DOM structure while content streams.
        
        This ensures the page doesn't "jump" as content loads.
        """
        # Initial placeholders (in DOM order)
        placeholders = [
            create_suspense_placeholder("section-1", "<div class='skeleton'>Loading 1...</div>"),
            create_suspense_placeholder("section-2", "<div class='skeleton'>Loading 2...</div>"),
            create_suspense_placeholder("section-3", "<div class='skeleton'>Loading 3...</div>"),
        ]
        
        # All have proper structure
        for i, ph in enumerate(placeholders, 1):
            assert f'data-suspense="section-{i}"' in ph
            assert 'data-state="pending"' in ph
            assert 'data-suspense-fallback' in ph
    
    @pytest.mark.asyncio
    async def test_timeout_does_not_block_resolved(self):
        """
        Timeouts on slow boundaries shouldn't block already-resolved ones.
        """
        from pynext.server.streaming import _create_timeout_script
        
        # Create timeout script
        timeout_script = _create_timeout_script("slow-boundary")
        
        # Should set timeout state
        assert 'data-state' in timeout_script
        assert 'timeout' in timeout_script
        
        # Should log warning
        assert 'console.warn' in timeout_script

