"""
Tests for pynext/devtools/processor.py - AI Session Analysis.

These tests cover:
- Session data loading
- Key frame extraction
- Diagnosis generation
- Briefing document generation
- Storyboard creation
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch, AsyncMock

from pynext.devtools.processor import (
    SessionProcessor,
    AnalysisResult,
    Diagnosis,
    FrameNarration,
    ANALYSIS_MODEL,
)


class TestSessionProcessorInit:
    """Test SessionProcessor initialization."""
    
    def test_init_with_api_key(self):
        """Processor accepts API key directly."""
        processor = SessionProcessor(api_key="sk-test-key")
        assert processor.api_key == "sk-test-key"
    
    def test_init_without_api_key_uses_env(self):
        """Processor falls back to environment variable."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-env-key"}):
            processor = SessionProcessor()
            assert processor.api_key == "sk-env-key"
    
    def test_model_is_claude_4_5_opus(self):
        """Processor uses Claude 4.5 Opus model."""
        processor = SessionProcessor(api_key="test")
        assert processor.model == ANALYSIS_MODEL
        assert "opus" in processor.model.lower()


class TestDiagnosis:
    """Test Diagnosis dataclass."""
    
    def test_diagnosis_basic(self):
        """Diagnosis stores bug information."""
        diag = Diagnosis(
            bug_type="framework_bug",
            root_cause="Handler not attached during hydration",
            source_file="signals.js",
            source_line=450,
            severity="high",
            confidence=0.85,
        )
        
        assert diag.bug_type == "framework_bug"
        assert diag.source_file == "signals.js"
        assert diag.confidence == 0.85
    
    def test_diagnosis_to_dict(self):
        """Diagnosis serializes to dictionary."""
        diag = Diagnosis(
            bug_type="app_bug",
            root_cause="Missing validator",
            recommended_actions=["Add validator", "Test form"],
        )
        
        data = diag.to_dict()
        
        assert data["bug_type"] == "app_bug"
        assert len(data["recommended_actions"]) == 2


class TestAnalysisResult:
    """Test AnalysisResult dataclass."""
    
    def test_analysis_result_basic(self):
        """AnalysisResult stores analysis data."""
        result = AnalysisResult(
            session_id="rec_123",
            session_path=Path("/tmp/session"),
        )
        
        assert result.session_id == "rec_123"
        assert result.model_used == ANALYSIS_MODEL
    
    def test_analysis_result_with_files(self):
        """AnalysisResult tracks generated file paths."""
        result = AnalysisResult(
            session_id="rec_123",
            session_path=Path("/tmp/session"),
            briefing_path=Path("/tmp/session/briefing.md"),
            narration_path=Path("/tmp/session/narration.json"),
        )
        
        assert result.briefing_path is not None
        assert result.briefing_path.name == "briefing.md"


class TestFrameNarration:
    """Test FrameNarration dataclass."""
    
    def test_frame_narration_basic(self):
        """FrameNarration stores frame description."""
        narration = FrameNarration(
            frame_number=1,
            timestamp_ms=500,
            screenshot_path="key_frames/0001.png",
            narration="Modal dialog is open with form inputs visible.",
            is_key_frame=True,
        )
        
        assert narration.frame_number == 1
        assert "Modal dialog" in narration.narration
        assert narration.is_key_frame is True


class TestLoadSessionData:
    """Test session data loading."""
    
    def test_load_session_data(self):
        """Session data is loaded from summary.json."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            session_dir.mkdir()
            
            summary_data = {
                "session_id": "rec_123",
                "intent": "Testing form",
                "outcome": "Form broken",
            }
            
            with open(session_dir / "summary.json", "w") as f:
                json.dump(summary_data, f)
            
            processor = SessionProcessor(api_key="test")
            data = processor._load_session_data(session_dir)
            
            assert data["session_id"] == "rec_123"
            assert data["intent"] == "Testing form"
    
    def test_load_missing_session_data(self):
        """Missing summary.json returns empty dict."""
        with TemporaryDirectory() as tmpdir:
            processor = SessionProcessor(api_key="test")
            data = processor._load_session_data(Path(tmpdir))
            
            assert data == {}


class TestBriefingGeneration:
    """Test briefing document generation."""
    
    def test_generate_basic_briefing(self):
        """Basic briefing is generated without AI."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            session_dir.mkdir()
            
            session_data = {
                "session_id": "rec_test",
                "intent": "Test intent",
                "outcome": "Test outcome",
                "duration_ms": 5000,
                "notes": [{"ts": 100, "text": "Test note"}],
                "key_events": [{"ts": 0, "event": "session_start"}],
            }
            
            processor = SessionProcessor(api_key="test")
            path = processor._generate_basic_briefing(session_dir, session_data, "No API key")
            
            assert path.exists()
            content = path.read_text()
            assert "Test intent" in content
            assert "Test outcome" in content
            assert "Test note" in content
    
    def test_generate_briefing_with_diagnosis(self):
        """Full briefing includes diagnosis."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            session_dir.mkdir()
            
            session_data = {
                "session_id": "rec_test",
                "intent": "Testing form",
                "outcome": "Broken",
                "duration_ms": 1000,
                "notes": [],
                "key_events": [],
            }
            
            diagnosis = Diagnosis(
                bug_type="framework_bug",
                root_cause="Handler not attached",
                severity="high",
                confidence=0.9,
                explanation="The oninput handler was not attached during hydration.",
                recommended_actions=["Check signals.js line 450"],
            )
            
            result = AnalysisResult(
                session_id="rec_test",
                session_path=session_dir,
                diagnosis=diagnosis,
            )
            
            processor = SessionProcessor(api_key="test")
            path = processor._generate_briefing(session_dir, session_data, result)
            
            assert path.exists()
            content = path.read_text()
            assert "framework_bug" in content
            assert "Handler not attached" in content
            assert "signals.js" in content


class TestInstructionsGeneration:
    """Test instructions meta-prompt generation."""
    
    def test_generate_instructions(self):
        """Instructions.md is generated correctly."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            session_dir.mkdir()
            
            processor = SessionProcessor(api_key="test")
            path = processor._generate_instructions(session_dir, {})
            
            assert path.exists()
            content = path.read_text()
            
            # Check for key sections
            assert "How to Read This Debug Session" in content
            assert "briefing.md" in content
            assert "storyboard.png" in content
            assert "NO_CHANGE" in content


class TestNarrationGeneration:
    """Test narration file generation."""
    
    def test_generate_narration_file(self):
        """Narration.json is generated correctly."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            session_dir.mkdir()
            
            result = AnalysisResult(
                session_id="rec_test",
                session_path=session_dir,
                frame_narrations=[
                    FrameNarration(
                        frame_number=1,
                        timestamp_ms=0,
                        screenshot_path="0001.png",
                        narration="Initial state",
                        is_key_frame=True,
                    ),
                    FrameNarration(
                        frame_number=5,
                        timestamp_ms=500,
                        screenshot_path="0005.png",
                        narration="Button clicked",
                    ),
                ],
            )
            
            processor = SessionProcessor(api_key="test")
            path = processor._generate_narration_file(session_dir, result)
            
            assert path.exists()
            with open(path) as f:
                data = json.load(f)
            
            assert data["frame_count"] == 2
            assert len(data["frames"]) == 2
            assert data["frames"][0]["narration"] == "Initial state"


class TestDiagnosisPrompt:
    """Test diagnosis prompt building."""
    
    def test_build_diagnosis_prompt(self):
        """Diagnosis prompt includes session data."""
        session_data = {
            "intent": "Test form input",
            "outcome": "Input not working",
            "duration_ms": 5000,
            "notes": [{"ts": 100, "text": "Can't type"}],
            "key_events": [
                {"ts": 0, "event": "session_start"},
                {"ts": 100, "event": "click", "target": "#input"},
            ],
        }
        
        processor = SessionProcessor(api_key="test")
        prompt = processor._build_diagnosis_prompt(session_data)
        
        assert "Test form input" in prompt
        assert "Input not working" in prompt
        assert "Can't type" in prompt
        assert "JSON" in prompt  # Asks for JSON response


class TestDiagnosisResponseParsing:
    """Test parsing Claude's diagnosis response."""
    
    def test_parse_json_response(self):
        """JSON response is parsed correctly."""
        response = '''Based on my analysis:
        
```json
{
    "bug_type": "framework_bug",
    "root_cause": "Handler not attached during hydration",
    "source_file": "signals.js",
    "source_line": 450,
    "severity": "high",
    "confidence": 0.85,
    "explanation": "The oninput handler was not attached.",
    "recommended_actions": ["Fix line 450", "Add test"]
}
```
'''
        
        processor = SessionProcessor(api_key="test")
        diag = processor._parse_diagnosis_response(response)
        
        assert diag.bug_type == "framework_bug"
        assert diag.source_file == "signals.js"
        assert diag.source_line == 450
        assert diag.confidence == 0.85
        assert len(diag.recommended_actions) == 2
    
    def test_parse_malformed_json(self):
        """Malformed JSON falls back to text extraction."""
        response = "The bug appears to be a hydration issue."
        
        processor = SessionProcessor(api_key="test")
        diag = processor._parse_diagnosis_response(response)
        
        assert diag.bug_type == "unknown"
        assert "hydration" in diag.root_cause.lower()


class TestKeyFrameLoading:
    """Test key frame screenshot loading."""
    
    def test_load_key_frames_from_directory(self):
        """Key frames are loaded from key_frames directory."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            key_frames_dir = session_dir / "key_frames"
            key_frames_dir.mkdir(parents=True)
            
            # Create fake PNG files
            for i in [1, 5, 10]:
                png_path = key_frames_dir / f"{i:04d}.png"
                png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)
            
            processor = SessionProcessor(api_key="test")
            frames = processor._load_key_frames(session_dir, {"key_frames": [1, 5, 10]})
            
            assert len(frames) == 3
            assert all("data" in f for f in frames)
    
    def test_load_fallback_to_all_frames(self):
        """Falls back to all_frames if no key_frames."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            all_frames_dir = session_dir / "all_frames"
            all_frames_dir.mkdir(parents=True)
            
            # Create 5 fake PNGs
            for i in range(1, 6):
                png_path = all_frames_dir / f"{i:04d}.png"
                png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)
            
            processor = SessionProcessor(api_key="test")
            frames = processor._load_key_frames(session_dir, {})
            
            # Should sample first, middle, last = 3 frames
            assert len(frames) == 3


class TestKeyInsights:
    """Test key insight extraction."""
    
    def test_extract_no_change_events(self):
        """NO_CHANGE events are flagged as insights."""
        session_data = {
            "key_events": [
                {"ts": 100, "event": "keypress", "result": "NO_CHANGE"},
            ]
        }
        
        processor = SessionProcessor(api_key="test")
        insights = processor._extract_key_insights(session_data, None)
        
        assert any("no effect" in i.lower() for i in insights)
    
    def test_extract_notes_as_insights(self):
        """User notes become insights."""
        session_data = {
            "key_events": [
                {"ts": 100, "event": "note", "text": "Bug found here"},
            ]
        }
        
        processor = SessionProcessor(api_key="test")
        insights = processor._extract_key_insights(session_data, None)
        
        assert any("Bug found here" in i for i in insights)


class TestAnalyzeSessionIntegration:
    """Integration tests for full session analysis."""
    
    @pytest.mark.asyncio
    async def test_analyze_session_without_api(self):
        """Session analysis works without API (basic mode)."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            session_dir.mkdir()
            (session_dir / "all_frames").mkdir()
            (session_dir / "key_frames").mkdir()
            
            # Create summary
            summary = {
                "session_id": "rec_test",
                "intent": "Test",
                "outcome": "Done",
                "duration_ms": 1000,
                "notes": [],
                "key_events": [],
            }
            with open(session_dir / "summary.json", "w") as f:
                json.dump(summary, f)
            
            # Create processor without valid API key
            processor = SessionProcessor(api_key=None)
            
            # Should still generate basic briefing
            result = await processor.analyze_session(session_dir)
            
            assert result.session_id == "rec_test"
            assert result.briefing_path is not None
            assert result.briefing_path.exists()
    
    @pytest.mark.asyncio
    async def test_analyze_session_with_mock_api(self):
        """Session analysis with mocked API calls."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            session_dir.mkdir()
            (session_dir / "key_frames").mkdir()
            
            # Create a fake screenshot
            png_path = session_dir / "key_frames" / "0001.png"
            png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            
            summary = {
                "session_id": "rec_test",
                "intent": "Test form",
                "outcome": "Form broken",
                "duration_ms": 5000,
                "notes": [{"ts": 100, "text": "Can't type"}],
                "key_events": [{"ts": 0, "event": "session_start"}],
            }
            with open(session_dir / "summary.json", "w") as f:
                json.dump(summary, f)
            
            # Mock the Anthropic client
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = '''```json
{
    "bug_type": "framework_bug",
    "root_cause": "Handler not attached",
    "severity": "high",
    "confidence": 0.9,
    "explanation": "Hydration failed",
    "recommended_actions": ["Check signals.js"]
}
```'''
            
            processor = SessionProcessor(api_key="sk-test")
            
            with patch.object(processor, "_get_client") as mock_get_client:
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                result = await processor.analyze_session(session_dir)
            
            assert result.diagnosis is not None
            assert result.diagnosis.bug_type == "framework_bug"
            assert result.briefing_path.exists()


class TestStoryboardGeneration:
    """Test storyboard composite image generation."""
    
    def test_storyboard_without_pil(self):
        """Storyboard generation handles missing PIL."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            session_dir.mkdir()
            
            processor = SessionProcessor(api_key="test")
            
            with patch.dict("sys.modules", {"PIL": None}):
                result = processor._generate_storyboard(session_dir, {}, [])
            
            # Should return None when no frames
            assert result is None
    
    def test_storyboard_with_no_frames(self):
        """Storyboard returns None with no frames."""
        with TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_1"
            session_dir.mkdir()
            
            processor = SessionProcessor(api_key="test")
            result = processor._generate_storyboard(session_dir, {}, [])
            
            assert result is None


class TestModelConfiguration:
    """Test model configuration."""
    
    def test_uses_claude_opus_4_5(self):
        """Processor uses the correct model."""
        assert "opus" in ANALYSIS_MODEL.lower()
        assert "4" in ANALYSIS_MODEL or "4-5" in ANALYSIS_MODEL

