"""
Semantic Retriever - Search over PyNext knowledge base.

Provides semantic search using embeddings to find relevant
documentation, code examples, and patterns.

Example:
    retriever = SemanticRetriever(indexer, embeddings)
    
    # Basic search
    results = retriever.search("drag and drop component")
    
    # Search for feature implementation
    context = retriever.search_for_feature("authentication with sessions")
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import logging

from .indexer import KnowledgeIndexer, IndexedChunk
from .embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """
    A single search result.
    
    Attributes:
        chunk: The matched chunk
        score: Relevance score (0-1, higher is better)
        highlights: Key matching phrases
    """
    chunk: IndexedChunk
    score: float
    highlights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "highlights": self.highlights,
        }


@dataclass
class FeatureContext:
    """
    Complete context for implementing a feature.
    
    Attributes:
        documentation: Relevant doc sections
        examples: Code examples
        api_signatures: Relevant API signatures
        patterns: Applicable patterns
        imports: Required imports
    """
    documentation: List[RetrievalResult] = field(default_factory=list)
    examples: List[RetrievalResult] = field(default_factory=list)
    api_signatures: List[RetrievalResult] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    
    def to_prompt_context(self, max_tokens: int = 4000) -> str:
        """Format as context for AI prompt."""
        sections = []
        
        if self.documentation:
            sections.append("## Relevant Documentation\n")
            for result in self.documentation[:3]:
                sections.append(f"### From {result.chunk.source}\n")
                sections.append(result.chunk.content[:1000])
                sections.append("\n")
        
        if self.examples:
            sections.append("\n## Code Examples\n")
            for result in self.examples[:3]:
                sections.append("```python\n")
                sections.append(result.chunk.content[:800])
                sections.append("\n```\n")
        
        if self.api_signatures:
            sections.append("\n## API Reference\n")
            for result in self.api_signatures[:5]:
                sections.append("```python\n")
                sections.append(result.chunk.content)
                sections.append("\n```\n")
        
        if self.imports:
            sections.append("\n## Required Imports\n")
            sections.append("```python\n")
            sections.append("\n".join(self.imports))
            sections.append("\n```\n")
        
        context = "\n".join(sections)
        
        # Truncate if too long (rough token estimate)
        if len(context) > max_tokens * 4:
            context = context[:max_tokens * 4]
        
        return context


class SemanticRetriever:
    """
    Semantic search over PyNext knowledge base.
    
    Uses embeddings to find semantically similar content,
    not just keyword matches.
    
    Attributes:
        indexer: Knowledge indexer with chunks
        embeddings: Embedding provider
    """
    
    def __init__(
        self,
        indexer: KnowledgeIndexer,
        embeddings: Optional[EmbeddingProvider] = None,
    ):
        """
        Initialize retriever.
        
        Args:
            indexer: KnowledgeIndexer with indexed chunks
            embeddings: EmbeddingProvider for query encoding
        """
        self.indexer = indexer
        self.embeddings = embeddings
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        Search for relevant PyNext knowledge.
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            filters: Optional filters (chunk_type, topics)
        
        Returns:
            List of RetrievalResult ranked by relevance
        """
        # Get candidate chunks
        chunks = self.indexer.chunks
        
        # Apply filters
        if filters:
            if "chunk_type" in filters:
                chunks = [c for c in chunks if c.chunk_type == filters["chunk_type"]]
            if "topics" in filters:
                filter_topics = set(filters["topics"])
                chunks = [c for c in chunks if set(c.topics) & filter_topics]
        
        if not chunks:
            return []
        
        # Score each chunk
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for chunk in chunks:
            # Combine keyword and semantic scoring
            keyword_score = self._keyword_score(query_words, chunk)
            
            # If we have embeddings, use semantic scoring
            semantic_score = 0.0
            if self.embeddings and chunk.embedding:
                # We'll compute query embedding lazily
                semantic_score = self._semantic_score_sync(query, chunk)
            
            # Combined score (weight semantic higher if available)
            if semantic_score > 0:
                score = 0.3 * keyword_score + 0.7 * semantic_score
            else:
                score = keyword_score
            
            if score > 0.1:  # Minimum threshold
                highlights = self._extract_highlights(query_words, chunk)
                results.append(RetrievalResult(
                    chunk=chunk,
                    score=score,
                    highlights=highlights,
                ))
        
        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results[:top_k]
    
    async def search_async(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        Async version of search with semantic scoring.
        
        Args:
            query: Natural language query
            top_k: Number of results
            filters: Optional filters
        
        Returns:
            List of RetrievalResult
        """
        # Get candidate chunks
        chunks = self.indexer.chunks
        
        # Apply filters
        if filters:
            if "chunk_type" in filters:
                chunks = [c for c in chunks if c.chunk_type == filters["chunk_type"]]
            if "topics" in filters:
                filter_topics = set(filters["topics"])
                chunks = [c for c in chunks if set(c.topics) & filter_topics]
        
        if not chunks:
            return []
        
        # Get query embedding
        query_embedding = None
        if self.embeddings:
            query_embedding = await self.embeddings.embed(query)
        
        # Score each chunk
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for chunk in chunks:
            keyword_score = self._keyword_score(query_words, chunk)
            
            semantic_score = 0.0
            if query_embedding and chunk.embedding:
                semantic_score = self._cosine_similarity(query_embedding, chunk.embedding)
            
            if semantic_score > 0:
                score = 0.3 * keyword_score + 0.7 * semantic_score
            else:
                score = keyword_score
            
            if score > 0.1:
                highlights = self._extract_highlights(query_words, chunk)
                results.append(RetrievalResult(
                    chunk=chunk,
                    score=score,
                    highlights=highlights,
                ))
        
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
    
    def search_for_feature(self, feature: str) -> FeatureContext:
        """
        Search for everything needed to implement a feature.
        
        Args:
            feature: Feature description
        
        Returns:
            FeatureContext with docs, examples, APIs, patterns
        """
        context = FeatureContext()
        
        # Search documentation
        doc_results = self.search(
            feature,
            top_k=5,
            filters={"chunk_type": "docs"},
        )
        context.documentation = doc_results
        
        # Search examples
        example_results = self.search(
            feature,
            top_k=5,
            filters={"chunk_type": "example"},
        )
        context.examples = example_results
        
        # Search API signatures
        api_results = self.search(
            feature,
            top_k=10,
            filters={"chunk_type": "api"},
        )
        context.api_signatures = api_results
        
        # Extract imports from results
        imports = self._extract_imports_from_results(doc_results + example_results)
        context.imports = list(imports)
        
        # Identify patterns
        context.patterns = self._identify_patterns(feature)
        
        return context
    
    def search_by_intent(self, intent: str) -> List[RetrievalResult]:
        """
        Search based on developer intent.
        
        Intents like:
        - "create page"
        - "add authentication"
        - "database query"
        - "websocket connection"
        
        Args:
            intent: Developer intent string
        
        Returns:
            Relevant chunks for that intent
        """
        # Map intents to search queries and filters
        intent_mapping = {
            "create page": ("page routing file-based", {"topics": ["routing"]}),
            "add auth": ("authentication login session", {"topics": ["auth"]}),
            "database": ("table model query postgresql", {"topics": ["database"]}),
            "api route": ("api endpoint request response", {"topics": ["api"]}),
            "component": ("component element div button", {"topics": ["components"]}),
            "island": ("island interactive hydration client", {"topics": ["islands"]}),
            "state": ("signal state computed effect", {"topics": ["state"]}),
            "realtime": ("websocket realtime live subscription", {"topics": ["realtime"]}),
            "form": ("form input validation action", {"topics": ["forms"]}),
            "style": ("css tailwind class theme", {"topics": ["styling"]}),
        }
        
        # Find matching intent
        intent_lower = intent.lower()
        query = intent
        filters = None
        
        for key, (search_query, search_filters) in intent_mapping.items():
            if key in intent_lower:
                query = search_query
                filters = search_filters
                break
        
        return self.search(query, top_k=10, filters=filters)
    
    def _keyword_score(self, query_words: Set[str], chunk: IndexedChunk) -> float:
        """Calculate keyword-based relevance score."""
        content_lower = chunk.content.lower()
        
        # Count matching words
        matches = sum(1 for word in query_words if word in content_lower)
        
        if not query_words:
            return 0.0
        
        # Base score from word matches
        base_score = matches / len(query_words)
        
        # Boost for metadata matches
        if chunk.metadata:
            name = chunk.metadata.get("name", "").lower()
            header = chunk.metadata.get("header", "").lower()
            
            if any(word in name for word in query_words):
                base_score += 0.2
            if any(word in header for word in query_words):
                base_score += 0.1
        
        # Boost for topic matches
        for topic in chunk.topics:
            if topic in query_words:
                base_score += 0.15
        
        return min(base_score, 1.0)
    
    def _semantic_score_sync(self, query: str, chunk: IndexedChunk) -> float:
        """
        Calculate semantic similarity (sync version).
        
        Note: This is a simplified version that uses keyword overlap
        when embeddings aren't pre-computed for the query.
        """
        if not chunk.embedding:
            return 0.0
        
        # In sync mode, fall back to keyword-based scoring
        # Full semantic scoring requires async for query embedding
        return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _extract_highlights(
        self,
        query_words: Set[str],
        chunk: IndexedChunk,
    ) -> List[str]:
        """Extract highlighted matching phrases."""
        highlights = []
        content = chunk.content
        
        # Find sentences containing query words
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(word in sentence.lower() for word in query_words):
                if len(sentence) > 20 and len(sentence) < 200:
                    highlights.append(sentence)
        
        return highlights[:3]
    
    def _extract_imports_from_results(
        self,
        results: List[RetrievalResult],
    ) -> Set[str]:
        """Extract import statements from results."""
        imports = set()
        
        import_patterns = [
            r'from pynext[.\w]* import [\w, ]+',
            r'from pynext import [\w, ]+',
            r'import pynext[.\w]*',
        ]
        
        import re
        for result in results:
            content = result.chunk.content
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.update(matches)
        
        return imports
    
    def _identify_patterns(self, feature: str) -> List[str]:
        """Identify relevant patterns for a feature."""
        feature_lower = feature.lower()
        patterns = []
        
        pattern_keywords = {
            "basic_page": ["page", "route"],
            "page_with_data": ["data", "fetch", "async"],
            "island_component": ["interactive", "island", "client"],
            "signal_state": ["state", "signal", "reactive"],
            "database_model": ["database", "model", "table"],
            "api_crud": ["api", "crud", "endpoint"],
            "auth_middleware": ["auth", "login", "protected"],
            "websocket_connection": ["websocket", "realtime", "live"],
            "form_action": ["form", "submit", "action"],
        }
        
        for pattern_name, keywords in pattern_keywords.items():
            if any(kw in feature_lower for kw in keywords):
                patterns.append(pattern_name)
        
        return patterns

