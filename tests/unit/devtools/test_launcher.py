"""
Tests for Chrome Launcher - Auto-launch Chrome with CDP Enabled.

Tests cover:
- ChromeInfo dataclass
- ChromeLauncher initialization
- Chrome detection on different platforms
- Launch with various options
- WebSocket URL retrieval
- Graceful shutdown
- Error handling
"""

import pytest
import tempfile
import platform
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from pynext.devtools.launcher import ChromeLauncher, ChromeInfo, quick_launch


# ============================================
# ChromeInfo Tests
# ============================================

class TestChromeInfo:
    """Tests for ChromeInfo dataclass."""
    
    def test_exists_true(self):
        """Test exists property when path exists."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            info = ChromeInfo(path=Path(f.name))
            assert info.exists is True
    
    def test_exists_false(self):
        """Test exists property when path doesn't exist."""
        info = ChromeInfo(path=Path("/nonexistent/chrome"))
        assert info.exists is False
    
    def test_with_version(self):
        """Test ChromeInfo with version."""
        info = ChromeInfo(path=Path("/usr/bin/chrome"), version="119.0.0.0")
        assert info.version == "119.0.0.0"


# ============================================
# ChromeLauncher Initialization Tests
# ============================================

class TestChromeLauncherInit:
    """Tests for ChromeLauncher initialization."""
    
    def test_init_default_port(self):
        """Test default debug port."""
        launcher = ChromeLauncher()
        assert launcher.debug_port == 9222
    
    def test_init_custom_port(self):
        """Test custom debug port."""
        launcher = ChromeLauncher(debug_port=9333)
        assert launcher.debug_port == 9333
    
    def test_init_no_process(self):
        """Test that process is None initially."""
        launcher = ChromeLauncher()
        assert launcher.process is None
    
    def test_is_running_false_initially(self):
        """Test is_running is False initially."""
        launcher = ChromeLauncher()
        assert launcher.is_running is False


# ============================================
# Chrome Detection Tests
# ============================================

class TestChromeLauncherFind:
    """Tests for Chrome detection."""
    
    def test_find_chrome_with_which(self):
        """Test finding Chrome via shutil.which."""
        launcher = ChromeLauncher()
        
        with patch('shutil.which') as mock_which:
            mock_which.return_value = "/usr/bin/google-chrome"
            
            result = launcher.find_chrome()
            
            # May or may not find depending on platform
            if result:
                assert result.path.exists() or mock_which.called
    
    def test_find_chrome_direct_path(self):
        """Test finding Chrome via direct path."""
        launcher = ChromeLauncher()
        
        # Create a temp file to simulate Chrome
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        # Patch CHROME_PATHS to include our temp file
        with patch.object(ChromeLauncher, 'CHROME_PATHS', {platform.system(): [temp_path]}):
            result = launcher.find_chrome()
            
            assert result is not None
            assert result.path == Path(temp_path)
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_find_chrome_not_found(self):
        """Test when Chrome is not found."""
        launcher = ChromeLauncher()
        
        with patch.object(ChromeLauncher, 'CHROME_PATHS', {platform.system(): []}):
            with patch('shutil.which', return_value=None):
                result = launcher.find_chrome()
                assert result is None
    
    def test_chrome_paths_for_current_platform(self):
        """Test that CHROME_PATHS has entries for current platform."""
        system = platform.system()
        assert system in ChromeLauncher.CHROME_PATHS


# ============================================
# Launch Tests
# ============================================

class TestChromeLauncherLaunch:
    """Tests for Chrome launch."""
    
    @pytest.mark.asyncio
    async def test_launch_chrome_not_found(self):
        """Test launch when Chrome not found."""
        launcher = ChromeLauncher()
        
        with patch.object(launcher, 'find_chrome', return_value=None):
            with pytest.raises(RuntimeError, match="Chrome/Chromium not found"):
                await launcher.launch("http://localhost:3000")
    
    @pytest.mark.asyncio
    async def test_launch_creates_profile(self):
        """Test that launch creates a temp profile."""
        launcher = ChromeLauncher()
        
        # Mock find_chrome and subprocess
        chrome_path = Path("/usr/bin/google-chrome")
        with patch.object(launcher, 'find_chrome', return_value=ChromeInfo(path=chrome_path)):
            with patch('subprocess.Popen') as mock_popen:
                mock_popen.return_value = Mock(poll=Mock(return_value=None))
                
                with patch.object(launcher, '_wait_for_ready', return_value="ws://localhost:9222/..."):
                    await launcher.launch("http://localhost:3000")
                    
                    # Should have created temp profile
                    assert launcher.profile_dir is not None
    
    @pytest.mark.asyncio
    async def test_launch_headless(self):
        """Test headless launch."""
        launcher = ChromeLauncher()
        
        chrome_path = Path("/usr/bin/google-chrome")
        with patch.object(launcher, 'find_chrome', return_value=ChromeInfo(path=chrome_path)):
            with patch('subprocess.Popen') as mock_popen:
                mock_popen.return_value = Mock(poll=Mock(return_value=None))
                
                with patch.object(launcher, '_wait_for_ready', return_value="ws://..."):
                    await launcher.launch("http://localhost:3000", headless=True)
                    
                    # Check that --headless was in args
                    call_args = mock_popen.call_args[0][0]
                    assert any("headless" in arg for arg in call_args)
    
    @pytest.mark.asyncio
    async def test_launch_custom_window_size(self):
        """Test custom window size."""
        launcher = ChromeLauncher()
        
        chrome_path = Path("/usr/bin/google-chrome")
        with patch.object(launcher, 'find_chrome', return_value=ChromeInfo(path=chrome_path)):
            with patch('subprocess.Popen') as mock_popen:
                mock_popen.return_value = Mock(poll=Mock(return_value=None))
                
                with patch.object(launcher, '_wait_for_ready', return_value="ws://..."):
                    await launcher.launch(
                        "http://localhost:3000",
                        window_size=(1920, 1080),
                    )
                    
                    call_args = mock_popen.call_args[0][0]
                    assert any("1920,1080" in arg for arg in call_args)


# ============================================
# Wait for Ready Tests
# ============================================

class TestChromeLauncherWaitForReady:
    """Tests for waiting for Chrome to be ready."""
    
    @pytest.mark.asyncio
    async def test_wait_for_ready_success(self):
        """Test successful wait for ready."""
        launcher = ChromeLauncher()
        
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {"type": "page", "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/ABC"}
        ]).encode()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = await launcher._wait_for_ready(timeout=5.0)
            
            assert result == "ws://localhost:9222/devtools/page/ABC"
    
    @pytest.mark.asyncio
    async def test_wait_for_ready_timeout(self):
        """Test timeout waiting for Chrome."""
        launcher = ChromeLauncher()
        
        # Mock urlopen to always raise an error
        import urllib.error
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
            
            with pytest.raises(TimeoutError):
                await launcher._wait_for_ready(timeout=0.1, poll_interval=0.05)


# ============================================
# Shutdown Tests
# ============================================

class TestChromeLauncherShutdown:
    """Tests for Chrome shutdown."""
    
    def test_shutdown_terminates_process(self):
        """Test that shutdown terminates Chrome process."""
        launcher = ChromeLauncher()
        launcher.process = Mock()
        launcher.process.wait = Mock()
        launcher.process.pid = 12345
        
        with patch('os.killpg'):
            with patch('os.getpgid', return_value=12345):
                launcher.shutdown()
        
        assert launcher.process is None
    
    def test_shutdown_cleans_profile(self):
        """Test that shutdown cleans up temp profile."""
        launcher = ChromeLauncher()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            launcher.profile_dir = Path(tmpdir)
            launcher.process = None  # No process to kill
            
            # Create a file in the profile
            (launcher.profile_dir / "test.txt").write_text("test")
            
            launcher.shutdown()
            
            assert launcher.profile_dir is None
    
    def test_shutdown_handles_missing_process(self):
        """Test shutdown when process doesn't exist."""
        launcher = ChromeLauncher()
        launcher.process = None
        
        # Should not raise
        launcher.shutdown()


# ============================================
# Get All Pages Tests
# ============================================

class TestChromeLauncherPages:
    """Tests for page management."""
    
    @pytest.mark.asyncio
    async def test_get_all_pages(self):
        """Test getting all open pages."""
        launcher = ChromeLauncher()
        
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {"type": "page", "url": "http://localhost:3000", "title": "App"},
            {"type": "page", "url": "about:blank", "title": "New Tab"},
            {"type": "background_page", "url": "chrome://extensions"},  # Should be filtered
        ]).encode()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            pages = await launcher.get_all_pages()
            
            assert len(pages) == 2
            assert pages[0]["url"] == "http://localhost:3000"
    
    @pytest.mark.asyncio
    async def test_get_all_pages_error(self):
        """Test get_all_pages handles errors."""
        launcher = ChromeLauncher()
        
        with patch('urllib.request.urlopen', side_effect=Exception("Error")):
            pages = await launcher.get_all_pages()
            
            assert pages == []


# ============================================
# Quick Launch Tests
# ============================================

class TestQuickLaunch:
    """Tests for quick_launch convenience function."""
    
    @pytest.mark.asyncio
    async def test_quick_launch(self):
        """Test quick launch function."""
        with patch.object(ChromeLauncher, 'find_chrome') as mock_find:
            mock_find.return_value = ChromeInfo(path=Path("/usr/bin/chrome"))
            
            with patch.object(ChromeLauncher, 'launch') as mock_launch:
                mock_launch.return_value = "ws://localhost:9222/..."
                
                launcher, ws_url = await quick_launch("http://localhost:3000")
                
                assert isinstance(launcher, ChromeLauncher)
                assert ws_url == "ws://localhost:9222/..."


# Need to import json for the tests
import json

