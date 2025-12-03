"""
Knowledge Indexer - Indexes all PyNext documentation and source code.

Creates semantic chunks from:
- Documentation (.md files)
- Source code (.py files) 
- Examples and tutorials
- API signatures

Example:
    indexer = KnowledgeIndexer()
    await indexer.index_all()
    
    chunks = indexer.get_chunks(chunk_type="docs")
"""

import ast
import hashlib
import json
import pickle
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class IndexedChunk:
    """
    A chunk of indexed content.
    
    Attributes:
        id: Unique identifier (hash of content + source)
        content: The actual text content
        source: File path where this came from
        chunk_type: Type - "docs", "code", "example", "api"
        metadata: Additional info (line numbers, headers, etc.)
        embedding: Vector embedding for semantic search
        topics: Extracted topics for filtering
    """
    id: str
    content: str
    source: str
    chunk_type: str  # "docs", "code", "example", "api"
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    topics: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "chunk_type": self.chunk_type,
            "metadata": self.metadata,
            "topics": self.topics,
            # Embedding stored separately for efficiency
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndexedChunk":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            source=data["source"],
            chunk_type=data["chunk_type"],
            metadata=data.get("metadata", {}),
            topics=data.get("topics", []),
        )


class KnowledgeIndexer:
    """
    Indexes all PyNext documentation and source code.
    
    The indexer creates semantic chunks optimized for retrieval:
    - Documentation is split by headers
    - Code is split by functions/classes
    - Examples are kept intact
    - API signatures are extracted cleanly
    
    Attributes:
        cache_dir: Directory for cached index
        embeddings: Embedding provider for vectors
        chunks: All indexed chunks
    """
    
    # Topics for classification
    TOPICS = {
        "routing": ["route", "page", "url", "path", "navigation", "link"],
        "state": ["signal", "state", "computed", "effect", "reactive"],
        "components": ["component", "element", "div", "button", "form"],
        "islands": ["island", "hydration", "interactive", "client"],
        "database": ["table", "model", "query", "database", "sql", "postgres"],
        "api": ["api", "endpoint", "request", "response", "rest"],
        "auth": ["auth", "login", "session", "user", "password"],
        "realtime": ["websocket", "realtime", "live", "subscription"],
        "styling": ["css", "tailwind", "style", "class", "theme"],
        "forms": ["form", "input", "validation", "action", "submit"],
    }
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        embeddings: Optional[Any] = None,
    ):
        """
        Initialize indexer.
        
        Args:
            cache_dir: Directory for cached index
            embeddings: EmbeddingProvider instance
        """
        self.cache_dir = cache_dir or Path(__file__).parent / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings = embeddings
        self.chunks: List[IndexedChunk] = []
        self._chunk_map: Dict[str, IndexedChunk] = {}
        
        # Find PyNext root
        self.pynext_root = self._find_pynext_root()
    
    def _find_pynext_root(self) -> Path:
        """Find the PyNext project root."""
        current = Path(__file__).parent
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent
        return Path.cwd()
    
    async def index_all(self, force: bool = False) -> None:
        """
        Build complete index of PyNext knowledge.
        
        Args:
            force: Rebuild even if cache exists
        """
        if not force and self.load_from_cache():
            logger.info("Loaded index from cache")
            return
        
        logger.info("Building knowledge index...")
        self.chunks = []
        self._chunk_map = {}
        
        # Index documentation
        docs_chunks = self._index_documentation()
        self.chunks.extend(docs_chunks)
        logger.info(f"Indexed {len(docs_chunks)} documentation chunks")
        
        # Index source code
        code_chunks = self._index_source_code()
        self.chunks.extend(code_chunks)
        logger.info(f"Indexed {len(code_chunks)} code chunks")
        
        # Index API signatures
        api_chunks = self._index_api_signatures()
        self.chunks.extend(api_chunks)
        logger.info(f"Indexed {len(api_chunks)} API signature chunks")
        
        # Build chunk map
        for chunk in self.chunks:
            self._chunk_map[chunk.id] = chunk
        
        # Generate embeddings if provider available
        if self.embeddings:
            await self._generate_embeddings()
        
        # Save to cache
        self.save_to_cache()
        logger.info(f"Total: {len(self.chunks)} chunks indexed")
    
    def _index_documentation(self) -> List[IndexedChunk]:
        """Index all documentation files."""
        chunks = []
        docs_path = self.pynext_root / "docs"
        
        if not docs_path.exists():
            return chunks
        
        for md_file in docs_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                file_chunks = self._chunk_markdown(content, str(md_file))
                chunks.extend(file_chunks)
            except Exception as e:
                logger.warning(f"Failed to index {md_file}: {e}")
        
        return chunks
    
    def _chunk_markdown(self, content: str, source: str) -> List[IndexedChunk]:
        """
        Split markdown into semantic chunks.
        
        Strategy:
        - Split by ## headers
        - Keep code blocks intact with their context
        - Extract examples separately
        """
        chunks = []
        
        # Split by headers
        sections = re.split(r'\n(?=## )', content)
        
        for section in sections:
            if not section.strip():
                continue
            
            # Extract header
            header_match = re.match(r'^##\s+(.+?)(?:\n|$)', section)
            header = header_match.group(1) if header_match else "Introduction"
            
            # Create chunk
            chunk_id = self._generate_id(section, source)
            topics = self._extract_topics(section)
            
            chunk = IndexedChunk(
                id=chunk_id,
                content=section.strip(),
                source=source,
                chunk_type="docs",
                metadata={
                    "header": header,
                    "has_code": "```" in section,
                },
                topics=topics,
            )
            chunks.append(chunk)
            
            # Also extract code blocks as separate chunks
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', section, re.DOTALL)
            for lang, code in code_blocks:
                if lang == "python" and len(code.strip()) > 50:
                    code_chunk = IndexedChunk(
                        id=self._generate_id(code, source + "_code"),
                        content=code.strip(),
                        source=source,
                        chunk_type="example",
                        metadata={
                            "language": lang or "python",
                            "context": header,
                        },
                        topics=topics,
                    )
                    chunks.append(code_chunk)
        
        return chunks
    
    def _index_source_code(self) -> List[IndexedChunk]:
        """Index PyNext source code."""
        chunks = []
        src_path = self.pynext_root / "pynext"
        
        if not src_path.exists():
            return chunks
        
        for py_file in src_path.rglob("*.py"):
            # Skip test files and caches
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding="utf-8")
                file_chunks = self._chunk_python(content, str(py_file))
                chunks.extend(file_chunks)
            except Exception as e:
                logger.warning(f"Failed to index {py_file}: {e}")
        
        return chunks
    
    def _chunk_python(self, content: str, source: str) -> List[IndexedChunk]:
        """
        Split Python code into semantic chunks.
        
        Strategy:
        - Extract module docstring
        - Extract class definitions with docstrings
        - Extract function definitions with docstrings
        """
        chunks = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return chunks
        
        # Module docstring
        if ast.get_docstring(tree):
            docstring = ast.get_docstring(tree)
            chunks.append(IndexedChunk(
                id=self._generate_id(docstring, source + "_module"),
                content=docstring,
                source=source,
                chunk_type="docs",
                metadata={"type": "module_docstring"},
                topics=self._extract_topics(docstring),
            ))
        
        # Classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                chunk = self._extract_class_chunk(node, content, source)
                if chunk:
                    chunks.append(chunk)
            
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions
                if hasattr(node, 'col_offset') and node.col_offset == 0:
                    chunk = self._extract_function_chunk(node, content, source)
                    if chunk:
                        chunks.append(chunk)
        
        return chunks
    
    def _extract_class_chunk(
        self,
        node: ast.ClassDef,
        content: str,
        source: str
    ) -> Optional[IndexedChunk]:
        """Extract a class definition as a chunk."""
        docstring = ast.get_docstring(node) or ""
        
        # Get class signature and docstring
        lines = content.split('\n')
        start_line = node.lineno - 1
        
        # Find end of docstring or first method
        end_line = start_line + 1
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = child.lineno - 1
                break
            end_line = getattr(child, 'end_lineno', end_line) or end_line
        
        class_content = '\n'.join(lines[start_line:min(end_line + 5, len(lines))])
        
        if len(class_content) < 20:
            return None
        
        return IndexedChunk(
            id=self._generate_id(class_content, source + f"_class_{node.name}"),
            content=class_content,
            source=source,
            chunk_type="code",
            metadata={
                "type": "class",
                "name": node.name,
                "docstring": docstring[:500] if docstring else "",
            },
            topics=self._extract_topics(class_content + " " + docstring),
        )
    
    def _extract_function_chunk(
        self,
        node: ast.FunctionDef,
        content: str,
        source: str
    ) -> Optional[IndexedChunk]:
        """Extract a function definition as a chunk."""
        docstring = ast.get_docstring(node) or ""
        
        lines = content.split('\n')
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', start_line + 20) or start_line + 20
        
        func_content = '\n'.join(lines[start_line:end_line])
        
        if len(func_content) < 20:
            return None
        
        return IndexedChunk(
            id=self._generate_id(func_content, source + f"_func_{node.name}"),
            content=func_content,
            source=source,
            chunk_type="code",
            metadata={
                "type": "function",
                "name": node.name,
                "docstring": docstring[:500] if docstring else "",
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            },
            topics=self._extract_topics(func_content + " " + docstring),
        )
    
    def _index_api_signatures(self) -> List[IndexedChunk]:
        """Extract clean API signatures."""
        chunks = []
        src_path = self.pynext_root / "pynext"
        
        if not src_path.exists():
            return chunks
        
        # Key modules to extract signatures from
        key_modules = [
            "core/__init__.py",
            "islands/__init__.py",
            "actions/__init__.py",
            "api/__init__.py",
            "db/table.py",
            "db/live/__init__.py",
        ]
        
        for module in key_modules:
            module_path = src_path / module
            if module_path.exists():
                try:
                    content = module_path.read_text(encoding="utf-8")
                    sigs = self._extract_signatures(content, str(module_path))
                    chunks.extend(sigs)
                except Exception as e:
                    logger.warning(f"Failed to extract sigs from {module}: {e}")
        
        return chunks
    
    def _extract_signatures(self, content: str, source: str) -> List[IndexedChunk]:
        """Extract function and class signatures."""
        chunks = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return chunks
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig = self._format_function_signature(node)
                if sig:
                    chunks.append(IndexedChunk(
                        id=self._generate_id(sig, source + f"_sig_{node.name}"),
                        content=sig,
                        source=source,
                        chunk_type="api",
                        metadata={
                            "type": "function_signature",
                            "name": node.name,
                        },
                        topics=self._extract_topics(sig),
                    ))
            
            elif isinstance(node, ast.ClassDef):
                sig = self._format_class_signature(node)
                if sig:
                    chunks.append(IndexedChunk(
                        id=self._generate_id(sig, source + f"_sig_{node.name}"),
                        content=sig,
                        source=source,
                        chunk_type="api",
                        metadata={
                            "type": "class_signature",
                            "name": node.name,
                        },
                        topics=self._extract_topics(sig),
                    ))
        
        return chunks
    
    def _format_function_signature(self, node: ast.FunctionDef) -> str:
        """Format a function signature."""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # Add defaults
        defaults = node.args.defaults
        if defaults:
            offset = len(args) - len(defaults)
            for i, default in enumerate(defaults):
                args[offset + i] += f" = {ast.unparse(default)}"
        
        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"
        
        prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        docstring = ast.get_docstring(node) or ""
        
        sig = f"{prefix}def {node.name}({', '.join(args)}){returns}"
        if docstring:
            sig += f'\n    """{docstring[:200]}..."""' if len(docstring) > 200 else f'\n    """{docstring}"""'
        
        return sig
    
    def _format_class_signature(self, node: ast.ClassDef) -> str:
        """Format a class signature."""
        bases = [ast.unparse(b) for b in node.bases] if node.bases else []
        bases_str = f"({', '.join(bases)})" if bases else ""
        
        docstring = ast.get_docstring(node) or ""
        
        sig = f"class {node.name}{bases_str}:"
        if docstring:
            sig += f'\n    """{docstring[:200]}..."""' if len(docstring) > 200 else f'\n    """{docstring}"""'
        
        return sig
    
    def _generate_id(self, content: str, source: str) -> str:
        """Generate unique ID for a chunk."""
        combined = f"{source}:{content[:100]}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from content for filtering."""
        content_lower = content.lower()
        topics = []
        
        for topic, keywords in self.TOPICS.items():
            if any(kw in content_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    async def _generate_embeddings(self) -> None:
        """Generate embeddings for all chunks."""
        if not self.embeddings:
            return
        
        logger.info("Generating embeddings...")
        
        # Batch embed for efficiency
        texts = [chunk.content for chunk in self.chunks]
        embeddings = await self.embeddings.embed_batch(texts)
        
        for chunk, embedding in zip(self.chunks, embeddings):
            chunk.embedding = embedding
        
        logger.info(f"Generated {len(embeddings)} embeddings")
    
    def save_to_cache(self) -> None:
        """Save index to cache."""
        # Save chunks (without embeddings)
        chunks_path = self.cache_dir / "chunks.json"
        chunks_data = [chunk.to_dict() for chunk in self.chunks]
        with open(chunks_path, "w") as f:
            json.dump(chunks_data, f)
        
        # Save embeddings separately
        if any(chunk.embedding for chunk in self.chunks):
            embeddings_path = self.cache_dir / "embeddings.pkl"
            embeddings_data = {
                chunk.id: chunk.embedding
                for chunk in self.chunks
                if chunk.embedding
            }
            with open(embeddings_path, "wb") as f:
                pickle.dump(embeddings_data, f)
        
        logger.info(f"Saved index to {self.cache_dir}")
    
    def load_from_cache(self) -> bool:
        """Load index from cache."""
        chunks_path = self.cache_dir / "chunks.json"
        embeddings_path = self.cache_dir / "embeddings.pkl"
        
        if not chunks_path.exists():
            return False
        
        try:
            # Load chunks
            with open(chunks_path, "r") as f:
                chunks_data = json.load(f)
            
            self.chunks = [IndexedChunk.from_dict(d) for d in chunks_data]
            
            # Load embeddings if available
            if embeddings_path.exists():
                with open(embeddings_path, "rb") as f:
                    embeddings_data = pickle.load(f)
                
                for chunk in self.chunks:
                    if chunk.id in embeddings_data:
                        chunk.embedding = embeddings_data[chunk.id]
            
            # Build chunk map
            self._chunk_map = {chunk.id: chunk for chunk in self.chunks}
            
            logger.info(f"Loaded {len(self.chunks)} chunks from cache")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return False
    
    def get_chunks(
        self,
        chunk_type: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ) -> List[IndexedChunk]:
        """
        Get chunks with optional filtering.
        
        Args:
            chunk_type: Filter by type (docs, code, example, api)
            topics: Filter by topics
        
        Returns:
            Filtered list of chunks
        """
        result = self.chunks
        
        if chunk_type:
            result = [c for c in result if c.chunk_type == chunk_type]
        
        if topics:
            result = [c for c in result if any(t in c.topics for t in topics)]
        
        return result
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[IndexedChunk]:
        """Get a specific chunk by ID."""
        return self._chunk_map.get(chunk_id)

