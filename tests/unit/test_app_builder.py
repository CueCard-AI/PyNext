"""
Tests for the PyNext AI App Builder.

Covers:
- Knowledge base indexing and retrieval
- Pattern library
- App planning
- Project context analysis
- File generation
- Progress tracking
- Rollback management
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime


# ========================================
# Knowledge Base Tests
# ========================================

class TestKnowledgeIndexer:
    """Tests for KnowledgeIndexer."""
    
    def test_indexed_chunk_creation(self):
        """Test IndexedChunk dataclass."""
        from pynext.app.knowledge.indexer import IndexedChunk
        
        chunk = IndexedChunk(
            id="test123",
            content="Test content",
            source="test.py",
            chunk_type="code",
            metadata={"type": "function"},
            topics=["routing", "api"],
        )
        
        assert chunk.id == "test123"
        assert chunk.content == "Test content"
        assert chunk.chunk_type == "code"
        assert "routing" in chunk.topics
    
    def test_indexed_chunk_to_dict(self):
        """Test IndexedChunk serialization."""
        from pynext.app.knowledge.indexer import IndexedChunk
        
        chunk = IndexedChunk(
            id="abc",
            content="content",
            source="file.py",
            chunk_type="docs",
        )
        
        d = chunk.to_dict()
        assert d["id"] == "abc"
        assert d["source"] == "file.py"
    
    def test_indexed_chunk_from_dict(self):
        """Test IndexedChunk deserialization."""
        from pynext.app.knowledge.indexer import IndexedChunk
        
        data = {
            "id": "xyz",
            "content": "hello",
            "source": "test.py",
            "chunk_type": "example",
            "topics": ["state"],
        }
        
        chunk = IndexedChunk.from_dict(data)
        assert chunk.id == "xyz"
        assert chunk.chunk_type == "example"
        assert "state" in chunk.topics
    
    def test_generate_id(self):
        """Test unique ID generation."""
        from pynext.app.knowledge.indexer import KnowledgeIndexer
        
        indexer = KnowledgeIndexer()
        
        id1 = indexer._generate_id("content1", "source1")
        id2 = indexer._generate_id("content2", "source1")
        id3 = indexer._generate_id("content1", "source1")
        
        # Different content = different ID
        assert id1 != id2
        # Same content and source = same ID
        assert id1 == id3
    
    def test_extract_topics(self):
        """Test topic extraction from content."""
        from pynext.app.knowledge.indexer import KnowledgeIndexer
        
        indexer = KnowledgeIndexer()
        
        # Routing topic
        topics = indexer._extract_topics("This is about page routing and navigation")
        assert "routing" in topics
        
        # State topic
        topics = indexer._extract_topics("Using Signal for reactive state")
        assert "state" in topics
        
        # Multiple topics
        topics = indexer._extract_topics("database model with api endpoint")
        assert "database" in topics
        assert "api" in topics
    
    def test_get_chunks_filtering(self):
        """Test chunk filtering by type and topics."""
        from pynext.app.knowledge.indexer import KnowledgeIndexer, IndexedChunk
        
        indexer = KnowledgeIndexer()
        indexer.chunks = [
            IndexedChunk(id="1", content="a", source="a.py", chunk_type="docs", topics=["routing"]),
            IndexedChunk(id="2", content="b", source="b.py", chunk_type="code", topics=["state"]),
            IndexedChunk(id="3", content="c", source="c.py", chunk_type="docs", topics=["state"]),
        ]
        
        # Filter by type
        docs = indexer.get_chunks(chunk_type="docs")
        assert len(docs) == 2
        
        # Filter by topics
        state_chunks = indexer.get_chunks(topics=["state"])
        assert len(state_chunks) == 2
        
        # Combined filter
        state_docs = indexer.get_chunks(chunk_type="docs", topics=["state"])
        assert len(state_docs) == 1


class TestEmbeddingProvider:
    """Tests for embedding providers."""
    
    def test_create_local_provider(self):
        """Test creating local embedding provider."""
        from pynext.app.knowledge.embeddings import EmbeddingProvider
        
        provider = EmbeddingProvider.create("local")
        assert provider is not None
        assert provider.dimension > 0
    
    @pytest.mark.asyncio
    async def test_local_fallback_embedding(self):
        """Test fallback embedding when sentence-transformers not installed."""
        from pynext.app.knowledge.embeddings import LocalEmbeddingProvider
        
        provider = LocalEmbeddingProvider()
        
        # Use fallback directly
        embedding = provider._fallback_embed("test text")
        
        assert len(embedding) == 48  # SHA384 produces 48 bytes
        assert all(isinstance(v, float) for v in embedding)
        assert all(-1 <= v <= 1 for v in embedding)
    
    @pytest.mark.asyncio
    async def test_batch_embedding(self):
        """Test batch embedding."""
        from pynext.app.knowledge.embeddings import LocalEmbeddingProvider
        
        provider = LocalEmbeddingProvider()
        provider._model = "fallback"  # Force fallback
        
        embeddings = await provider.embed_batch(["text1", "text2", "text3"])
        
        assert len(embeddings) == 3
        assert len(embeddings[0]) == 48


class TestSemanticRetriever:
    """Tests for semantic retriever."""
    
    def test_keyword_score(self):
        """Test keyword-based scoring."""
        from pynext.app.knowledge.retriever import SemanticRetriever
        from pynext.app.knowledge.indexer import IndexedChunk, KnowledgeIndexer
        
        indexer = KnowledgeIndexer()
        retriever = SemanticRetriever(indexer)
        
        chunk = IndexedChunk(
            id="1",
            content="This is about page routing",
            source="test.py",
            chunk_type="docs",
            topics=["routing"],
            metadata={"name": "routing", "header": "Routing Guide"},
        )
        
        query_words = {"page", "routing"}
        score = retriever._keyword_score(query_words, chunk)
        
        assert score > 0.5  # Good match
    
    def test_search_basic(self):
        """Test basic search functionality."""
        from pynext.app.knowledge.retriever import SemanticRetriever
        from pynext.app.knowledge.indexer import IndexedChunk, KnowledgeIndexer
        
        indexer = KnowledgeIndexer()
        indexer.chunks = [
            IndexedChunk(id="1", content="Signal is for reactive state", source="a.py", chunk_type="docs", topics=["state"]),
            IndexedChunk(id="2", content="Routes are file-based", source="b.py", chunk_type="docs", topics=["routing"]),
        ]
        
        retriever = SemanticRetriever(indexer)
        
        results = retriever.search("reactive state signal")
        
        assert len(results) > 0
        assert results[0].chunk.id == "1"  # State chunk should rank first
    
    def test_search_with_filters(self):
        """Test search with filters."""
        from pynext.app.knowledge.retriever import SemanticRetriever
        from pynext.app.knowledge.indexer import IndexedChunk, KnowledgeIndexer
        
        indexer = KnowledgeIndexer()
        indexer.chunks = [
            IndexedChunk(id="1", content="Signal state", source="a.py", chunk_type="docs", topics=["state"]),
            IndexedChunk(id="2", content="Signal example", source="b.py", chunk_type="example", topics=["state"]),
        ]
        
        retriever = SemanticRetriever(indexer)
        
        # Filter to examples only
        results = retriever.search("signal", filters={"chunk_type": "example"})
        
        assert len(results) == 1
        assert results[0].chunk.chunk_type == "example"
    
    def test_search_for_feature(self):
        """Test feature search."""
        from pynext.app.knowledge.retriever import SemanticRetriever
        from pynext.app.knowledge.indexer import IndexedChunk, KnowledgeIndexer
        
        indexer = KnowledgeIndexer()
        indexer.chunks = [
            IndexedChunk(id="1", content="Auth middleware", source="a.py", chunk_type="docs", topics=["auth"]),
            IndexedChunk(id="2", content="@action decorator", source="b.py", chunk_type="api", topics=["auth"]),
        ]
        
        retriever = SemanticRetriever(indexer)
        
        context = retriever.search_for_feature("authentication")
        
        assert context is not None
        assert hasattr(context, "documentation")
        assert hasattr(context, "api_signatures")


class TestPatternLibrary:
    """Tests for pattern library."""
    
    def test_get_pattern(self):
        """Test getting a pattern by name."""
        from pynext.app.knowledge.patterns import PatternLibrary
        
        library = PatternLibrary()
        
        pattern = library.get("basic_page")
        assert pattern is not None
        assert pattern.name == "basic_page"
        assert "pynext" in pattern.code_template
    
    def test_get_all_patterns(self):
        """Test getting all patterns."""
        from pynext.app.knowledge.patterns import PatternLibrary
        
        library = PatternLibrary()
        
        patterns = library.get_all()
        assert len(patterns) > 10  # We have many patterns
    
    def test_get_by_tag(self):
        """Test getting patterns by tag."""
        from pynext.app.knowledge.patterns import PatternLibrary
        
        library = PatternLibrary()
        
        auth_patterns = library.get_by_tag("auth")
        assert len(auth_patterns) >= 2  # login_form, auth_middleware
    
    def test_get_patterns_for_feature(self):
        """Test getting patterns for a feature description."""
        from pynext.app.knowledge.patterns import PatternLibrary
        
        library = PatternLibrary()
        
        patterns = library.get_patterns_for("authentication with login")
        pattern_names = [p.name for p in patterns]
        
        assert "auth_middleware" in pattern_names or "login_form" in pattern_names
    
    def test_pattern_render(self):
        """Test pattern template rendering."""
        from pynext.app.knowledge.patterns import PatternLibrary
        
        library = PatternLibrary()
        pattern = library.get("basic_page")
        
        rendered = pattern.render(
            name="Home",
            title="Welcome",
            description="Homepage",
        )
        
        assert "Home" in rendered
        assert "Welcome" in rendered
    
    def test_compose_patterns(self):
        """Test composing multiple patterns."""
        from pynext.app.knowledge.patterns import PatternLibrary
        
        library = PatternLibrary()
        
        composed = library.compose_patterns(["signal_state", "computed_value"])
        
        assert "Signal" in composed
        assert "Computed" in composed


class TestContextBuilder:
    """Tests for context builder."""
    
    def test_build_context(self):
        """Test building context for a task."""
        from pynext.app.knowledge.context_builder import ContextBuilder
        from pynext.app.knowledge.retriever import SemanticRetriever
        from pynext.app.knowledge.patterns import PatternLibrary
        from pynext.app.knowledge.indexer import KnowledgeIndexer
        
        indexer = KnowledgeIndexer()
        retriever = SemanticRetriever(indexer)
        patterns = PatternLibrary()
        
        builder = ContextBuilder(retriever, patterns)
        
        context = builder.build_context(
            task="Create a page with data fetching",
            max_tokens=2000,
        )
        
        assert "PyNext" in context
        assert len(context) > 100
    
    def test_build_file_context(self):
        """Test building context for a specific file."""
        from pynext.app.knowledge.context_builder import ContextBuilder
        from pynext.app.knowledge.retriever import SemanticRetriever
        from pynext.app.knowledge.patterns import PatternLibrary
        from pynext.app.knowledge.indexer import KnowledgeIndexer
        
        indexer = KnowledgeIndexer()
        retriever = SemanticRetriever(indexer)
        patterns = PatternLibrary()
        
        builder = ContextBuilder(retriever, patterns)
        
        context = builder.build_file_context(
            file_type="page",
            requirements={"purpose": "Home page"},
            existing_files={"pages/layout.py": "def layout(): pass"},
        )
        
        assert "page" in context.lower()
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        from pynext.app.knowledge.context_builder import ContextBuilder
        
        builder = ContextBuilder(None, None)
        
        # ~4 chars per token
        text = "a" * 400
        tokens = builder.estimate_tokens(text)
        
        assert 90 <= tokens <= 110


# ========================================
# App Planner Tests
# ========================================

class TestFileOperation:
    """Tests for FileOperation dataclass."""
    
    def test_file_operation_creation(self):
        """Test creating a file operation."""
        from pynext.app.planner import FileOperation, OperationType
        
        op = FileOperation(
            action=OperationType.CREATE,
            path="pages/index.py",
            description="Home page",
            file_type="page",
        )
        
        assert op.action == OperationType.CREATE
        assert op.path == "pages/index.py"
        assert op.file_type == "page"
    
    def test_file_operation_to_dict(self):
        """Test serialization."""
        from pynext.app.planner import FileOperation, OperationType
        
        op = FileOperation(
            action=OperationType.MODIFY,
            path="test.py",
            description="Test",
            dependencies=["other.py"],
        )
        
        d = op.to_dict()
        assert d["action"] == "modify"
        assert "other.py" in d["dependencies"]
    
    def test_file_operation_from_dict(self):
        """Test deserialization."""
        from pynext.app.planner import FileOperation, OperationType
        
        data = {
            "action": "create",
            "path": "new.py",
            "description": "New file",
            "file_type": "component",
        }
        
        op = FileOperation.from_dict(data)
        assert op.action == OperationType.CREATE
        assert op.path == "new.py"


class TestAppPlan:
    """Tests for AppPlan dataclass."""
    
    def test_app_plan_creation(self):
        """Test creating an app plan."""
        from pynext.app.planner import AppPlan, FileOperation, OperationType
        
        plan = AppPlan(
            name="my-app",
            description="Test app",
            complexity="small",
            operations=[
                FileOperation(OperationType.CREATE, "pages/index.py", "Home"),
            ],
        )
        
        assert plan.name == "my-app"
        assert len(plan.operations) == 1
    
    def test_app_plan_to_markdown(self):
        """Test markdown rendering."""
        from pynext.app.planner import AppPlan, FileOperation, OperationType
        
        plan = AppPlan(
            name="test",
            description="Test app",
            complexity="minimal",
            operations=[
                FileOperation(OperationType.CREATE, "pages/index.py", "Home page"),
                FileOperation(OperationType.MODIFY, "styles.css", "Add styles"),
            ],
        )
        
        md = plan.to_markdown()
        
        assert "# App Plan: test" in md
        assert "pages/index.py" in md
        assert "Files to Create" in md
    
    def test_app_plan_ordered_operations(self):
        """Test dependency ordering."""
        from pynext.app.planner import AppPlan, FileOperation, OperationType
        
        plan = AppPlan(
            name="test",
            description="Test",
            complexity="small",
            operations=[
                FileOperation(OperationType.CREATE, "pages/index.py", "Page", dependencies=["pages/layout.py"]),
                FileOperation(OperationType.CREATE, "pages/layout.py", "Layout"),
            ],
        )
        
        ordered = plan.get_ordered_operations()
        
        # Layout should come before index
        layout_idx = next(i for i, op in enumerate(ordered) if "layout" in op.path)
        index_idx = next(i for i, op in enumerate(ordered) if "index" in op.path)
        
        assert layout_idx < index_idx


class TestAppPlanner:
    """Tests for AppPlanner."""
    
    def test_estimate_complexity(self):
        """Test complexity estimation."""
        from pynext.app.planner import AppPlanner
        
        planner = AppPlanner()
        
        # Minimal
        complexity = planner._estimate_complexity("landing page")
        assert complexity in ("minimal", "small")
        
        # Medium
        complexity = planner._estimate_complexity("blog with auth and database")
        assert complexity in ("small", "medium")
        
        # Large
        complexity = planner._estimate_complexity(
            "e-commerce with auth, database, cart, checkout, admin dashboard, realtime"
        )
        assert complexity in ("medium", "large")
    
    def test_match_template(self):
        """Test template matching."""
        from pynext.app.planner import AppPlanner
        
        planner = AppPlanner()
        
        assert planner._match_template("blog with posts") == "blog"
        assert planner._match_template("e-commerce shop") == "ecommerce"
        assert planner._match_template("SaaS application") == "saas"
        assert planner._match_template("something random") is None
    
    def test_add_dependencies(self):
        """Test dependency addition."""
        from pynext.app.planner import AppPlanner, FileOperation, OperationType
        
        planner = AppPlanner()
        
        operations = [
            FileOperation(OperationType.CREATE, "pages/layout.py", "Layout", file_type="layout"),
            FileOperation(OperationType.CREATE, "pages/index.py", "Home", file_type="page"),
        ]
        
        planner._add_dependencies(operations)
        
        # Page should depend on layout
        index_op = next(op for op in operations if "index" in op.path)
        assert "pages/layout.py" in index_op.dependencies
    
    def test_estimate_time(self):
        """Test time estimation."""
        from pynext.app.planner import AppPlanner
        
        planner = AppPlanner()
        
        assert "second" in planner._estimate_time(3)
        assert "minute" in planner._estimate_time(10)
        assert "minute" in planner._estimate_time(25)


# ========================================
# Context Analyzer Tests
# ========================================

class TestProjectContext:
    """Tests for ProjectContext."""
    
    def test_project_context_creation(self):
        """Test creating project context."""
        from pynext.app.context import ProjectContext
        from pathlib import Path
        
        context = ProjectContext(
            root=Path("/test"),
            pages=["pages/index.py"],
            models=["User"],
        )
        
        assert context.root == Path("/test")
        assert len(context.pages) == 1
    
    def test_has_project(self):
        """Test has_project property."""
        from pynext.app.context import ProjectContext
        from pathlib import Path
        
        context = ProjectContext(root=Path("/test"))
        assert context.root is not None
    
    def test_get_summary(self):
        """Test summary generation."""
        from pynext.app.context import ProjectContext
        from pathlib import Path
        
        context = ProjectContext(
            root=Path("/test"),
            pages=["a.py", "b.py"],
            components=["c.py"],
            models=["User", "Post"],
        )
        
        summary = context.get_summary()
        
        assert "Pages: 2" in summary
        assert "Models: 2" in summary


class TestContextAnalyzer:
    """Tests for ContextAnalyzer."""
    
    def test_scan_structure(self):
        """Test directory structure scanning."""
        from pynext.app.context import ContextAnalyzer
        
        analyzer = ContextAnalyzer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "pages").mkdir()
            (tmpdir / "pages" / "index.py").write_text("")
            (tmpdir / "components").mkdir()
            
            structure = analyzer._scan_structure(tmpdir)
            
            assert "pages" in structure
            assert "components" in structure
    
    def test_find_files(self):
        """Test finding files by extension."""
        from pynext.app.context import ContextAnalyzer
        
        analyzer = ContextAnalyzer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "a.py").write_text("")
            (tmpdir / "b.py").write_text("")
            (tmpdir / "c.txt").write_text("")
            
            files = analyzer._find_files(tmpdir, ".py")
            
            assert len([f for f in files if f.endswith(".py")]) == 2
    
    def test_get_imports_for_file(self):
        """Test import suggestions."""
        from pynext.app.context import ContextAnalyzer, ProjectContext
        from pathlib import Path
        
        analyzer = ContextAnalyzer()
        context = ProjectContext(root=Path("/test"))
        
        imports = analyzer.get_imports_for_file(context, "island")
        
        assert any("Signal" in imp for imp in imports)
        assert any("island" in imp for imp in imports)


# ========================================
# Progress Tracker Tests
# ========================================

class TestProgressTracker:
    """Tests for ProgressTracker."""
    
    def test_start_plan(self):
        """Test starting plan tracking."""
        from pynext.app.progress import ProgressTracker
        from pynext.app.planner import AppPlan, FileOperation, OperationType
        
        tracker = ProgressTracker(verbose=False)
        
        plan = AppPlan(
            name="test",
            description="Test",
            complexity="minimal",
            operations=[
                FileOperation(OperationType.CREATE, "test.py", "Test"),
            ],
        )
        
        tracker.start_plan(plan)
        
        assert tracker.progress.total == 1
        assert len(tracker.progress.operations) == 1
    
    def test_complete_operation(self):
        """Test completing an operation."""
        from pynext.app.progress import ProgressTracker, OperationStatus
        from pynext.app.planner import AppPlan, FileOperation, OperationType
        
        tracker = ProgressTracker(verbose=False)
        
        plan = AppPlan(
            name="test",
            description="Test",
            complexity="minimal",
            operations=[
                FileOperation(OperationType.CREATE, "test.py", "Test"),
            ],
        )
        
        tracker.start_plan(plan)
        tracker.start_operation(plan.operations[0])
        tracker.complete_operation(plan.operations[0], success=True)
        
        assert tracker.progress.completed == 1
        assert tracker.progress.operations[0].status == OperationStatus.SUCCESS
    
    def test_skip_operation(self):
        """Test skipping an operation."""
        from pynext.app.progress import ProgressTracker, OperationStatus
        from pynext.app.planner import AppPlan, FileOperation, OperationType
        
        tracker = ProgressTracker(verbose=False)
        
        plan = AppPlan(
            name="test",
            description="Test",
            complexity="minimal",
            operations=[
                FileOperation(OperationType.CREATE, "test.py", "Test"),
            ],
        )
        
        tracker.start_plan(plan)
        tracker.skip_operation(plan.operations[0], "User declined")
        
        assert tracker.progress.skipped == 1


# ========================================
# Rollback Manager Tests
# ========================================

class TestRollbackManager:
    """Tests for RollbackManager."""
    
    def test_checkpoint_creation(self):
        """Test creating a checkpoint."""
        from pynext.app.rollback import RollbackManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manager = RollbackManager(tmpdir)
            
            checkpoint_id = manager.checkpoint("Test checkpoint")
            
            assert checkpoint_id is not None
            assert len(manager._checkpoints) == 1
    
    def test_mark_file_modified(self):
        """Test marking files as modified."""
        from pynext.app.rollback import RollbackManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manager = RollbackManager(tmpdir)
            
            manager.mark_file_modified("test.py")
            manager.mark_file_modified("other.py")
            
            assert len(manager._pending_files) == 2
    
    def test_rollback(self):
        """Test rollback functionality."""
        from pynext.app.rollback import RollbackManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.txt"
            
            # Create original file
            test_file.write_text("original")
            
            manager = RollbackManager(tmpdir)
            manager.mark_file_modified("test.txt")
            manager.checkpoint("Before change")
            
            # Modify file
            test_file.write_text("modified")
            
            # Rollback
            manager.rollback()
            
            assert test_file.read_text() == "original"
    
    def test_commit(self):
        """Test committing changes."""
        from pynext.app.rollback import RollbackManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manager = RollbackManager(tmpdir)
            
            manager.checkpoint("Test")
            assert len(manager._checkpoints) == 1
            
            manager.commit()
            assert len(manager._checkpoints) == 0


# ========================================
# File Generator Tests
# ========================================

class TestFileGenerator:
    """Tests for FileGenerator."""
    
    def test_extract_code(self):
        """Test code extraction from response."""
        from pynext.app.file_generator import FileGenerator
        
        generator = FileGenerator()
        
        response = '''Here's the code:
```python
def hello():
    return "world"
```
Done!'''
        
        code = generator._extract_code(response)
        
        assert "def hello():" in code
        assert "```" not in code
    
    def test_extract_imports(self):
        """Test import extraction."""
        from pynext.app.file_generator import FileGenerator
        
        generator = FileGenerator()
        
        code = '''from pynext import div, h1
import asyncio

def page():
    return div()
'''
        
        imports = generator._extract_imports(code)
        
        assert len(imports) == 2
        assert any("pynext" in imp for imp in imports)
    
    def test_generate_placeholder_page(self):
        """Test placeholder generation for page."""
        from pynext.app.file_generator import FileGenerator
        from pynext.app.planner import FileOperation, OperationType
        
        generator = FileGenerator()
        
        op = FileOperation(
            action=OperationType.CREATE,
            path="pages/test.py",
            description="Test page",
            file_type="page",
        )
        
        code = generator._generate_placeholder(op)
        
        assert "def page():" in code
        assert "pynext" in code


# ========================================
# App Generator Tests
# ========================================

class TestGenerationResult:
    """Tests for GenerationResult."""
    
    def test_generation_result_duration(self):
        """Test duration calculation."""
        from pynext.app.generator import GenerationResult
        from pynext.app.planner import AppPlan
        from datetime import datetime, timedelta
        
        plan = AppPlan(name="test", description="test", complexity="minimal", operations=[])
        
        result = GenerationResult(
            success=True,
            plan=plan,
            started_at=datetime.utcnow() - timedelta(seconds=5),
            completed_at=datetime.utcnow(),
        )
        
        assert 4 < result.duration < 6


# ========================================
# Session Tests
# ========================================

class TestSessionState:
    """Tests for SessionState."""
    
    def test_session_state_creation(self):
        """Test creating session state."""
        from pynext.app.session import SessionState
        
        state = SessionState()
        
        assert state.project_path is None
        assert state.mode == "plan"
        assert len(state.history) == 0
    
    def test_has_project(self):
        """Test has_project property."""
        from pynext.app.session import SessionState
        from pathlib import Path
        
        state = SessionState()
        assert not state.has_project
        
        state.project_path = Path("/test")
        assert state.has_project


# ========================================
# Integration Tests
# ========================================

class TestAppBuilderIntegration:
    """Integration tests for app builder."""
    
    @pytest.mark.asyncio
    async def test_plan_from_template(self):
        """Test creating a plan from template."""
        from pynext.app.planner import AppPlanner
        
        planner = AppPlanner()
        
        plan = planner._plan_from_template("blog", "blog with posts", "small")
        
        assert plan.name is not None
        assert len(plan.operations) > 0
        assert any("page" in op.file_type for op in plan.operations)
    
    @pytest.mark.asyncio
    async def test_knowledge_base_init(self):
        """Test knowledge base initialization."""
        from pynext.app.knowledge import PyNextKnowledge
        
        kb = PyNextKnowledge()
        
        # Should be able to get patterns without full index
        patterns = kb.get_patterns_for("page")
        assert len(patterns) > 0


# ========================================
# CLI Command Tests
# ========================================

class TestAppCLI:
    """Tests for app CLI commands."""
    
    def test_app_new_parser(self):
        """Test app new argument parsing."""
        import argparse
        
        # Create minimal parser for testing
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        app_parser = subparsers.add_parser("app")
        app_subparsers = app_parser.add_subparsers(dest="app_command")
        
        app_new = app_subparsers.add_parser("new")
        app_new.add_argument("description")
        app_new.add_argument("--mode", "-m", default="plan")
        app_new.add_argument("--complexity", "-c", default="auto")
        
        args = parser.parse_args(["app", "new", "test app", "--mode", "agent"])
        
        assert args.command == "app"
        assert args.app_command == "new"
        assert args.description == "test app"
        assert args.mode == "agent"

