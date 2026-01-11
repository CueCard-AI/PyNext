"""
Phase 34.4: Media Event Tests

Unit tests for media element event transpilation covering:
- play, pause, ended events
- timeupdate, loadeddata
- volumechange, seeking/seeked
- Media element properties

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestMediaPlaybackEvents:
    """Tests for media playback events."""
    
    def test_play_event(self):
        """play event should pass through."""
        code = '''
def on_play(event):
    update_play_button("playing")

video.addEventListener("play", on_play)
'''
        result = transpile(code)
        assert 'addEventListener("play"' in result
        assert '__py.' not in result
    
    def test_pause_event(self):
        """pause event should pass through."""
        code = '''
def on_pause(event):
    update_play_button("paused")

video.addEventListener("pause", on_pause)
'''
        result = transpile(code)
        assert 'addEventListener("pause"' in result
    
    def test_ended_event(self):
        """ended event should pass through."""
        code = '''
def on_ended(event):
    show_replay_button()
    log_watch_complete()

video.addEventListener("ended", on_ended)
'''
        result = transpile(code)
        assert 'addEventListener("ended"' in result


class TestMediaProgressEvents:
    """Tests for media progress events."""
    
    def test_timeupdate_event(self):
        """timeupdate event should pass through."""
        code = '''
def on_timeupdate(event):
    current = video.currentTime
    duration = video.duration
    progress = (current / duration) * 100
    update_progress_bar(progress)

video.addEventListener("timeupdate", on_timeupdate)
'''
        result = transpile(code)
        assert 'addEventListener("timeupdate"' in result
        assert 'video.currentTime' in result
        assert 'video.duration' in result
    
    def test_loadeddata_event(self):
        """loadeddata event should pass through."""
        code = '''
def on_loadeddata(event):
    duration = video.duration
    show_duration(duration)

video.addEventListener("loadeddata", on_loadeddata)
'''
        result = transpile(code)
        assert 'addEventListener("loadeddata"' in result


class TestMediaVolumeEvents:
    """Tests for media volume events."""
    
    def test_volumechange_event(self):
        """volumechange event should pass through."""
        code = '''
def on_volumechange(event):
    volume = video.volume
    muted = video.muted
    update_volume_ui(volume, muted)

video.addEventListener("volumechange", on_volumechange)
'''
        result = transpile(code)
        assert 'addEventListener("volumechange"' in result
        assert 'video.volume' in result
        assert 'video.muted' in result


class TestMediaSeekEvents:
    """Tests for media seek events."""
    
    def test_seeking_event(self):
        """seeking event should pass through."""
        code = '''
def on_seeking(event):
    show_loading_indicator()

video.addEventListener("seeking", on_seeking)
'''
        result = transpile(code)
        assert 'addEventListener("seeking"' in result
    
    def test_seeked_event(self):
        """seeked event should pass through."""
        code = '''
def on_seeked(event):
    hide_loading_indicator()

video.addEventListener("seeked", on_seeked)
'''
        result = transpile(code)
        assert 'addEventListener("seeked"' in result


class TestMediaPlayerPattern:
    """Tests for complete media player patterns."""
    
    def test_complete_player(self):
        """Complete media player should work."""
        code = '''
from pynext.client import document

def create_media_player(video_id):
    video = document.getElementById(video_id)
    
    def on_play(event):
        play_button.classList.add("playing")
    
    def on_pause(event):
        play_button.classList.remove("playing")
    
    def on_timeupdate(event):
        current = video.currentTime
        duration = video.duration
        percent = (current / duration) * 100
        progress.style.width = f"{percent}%"
    
    def on_ended(event):
        video.currentTime = 0
        play_button.classList.remove("playing")
    
    video.addEventListener("play", on_play)
    video.addEventListener("pause", on_pause)
    video.addEventListener("timeupdate", on_timeupdate)
    video.addEventListener("ended", on_ended)
'''
        result = transpile(code)
        assert 'video.currentTime' in result
        assert 'video.duration' in result
        assert result.count('addEventListener') == 4
    
    def test_canplay_event(self):
        """canplay event should pass through."""
        code = '''
def on_canplay(event):
    enable_play_button()

video.addEventListener("canplay", on_canplay)
'''
        result = transpile(code)
        assert 'addEventListener("canplay"' in result

