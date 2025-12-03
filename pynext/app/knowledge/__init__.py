"""
PyNext Knowledge Base - RAG system for PyNext code generation.

Since no LLM is natively trained on PyNext, this module provides:
- Semantic indexing of all PyNext docs and source code
- Pattern library with reusable code templates
- Context builder for optimal AI prompts
- Embedding support (local or API-based)

Example:
    from pynext.app.knowledge import PyNextKnowledge
    
    # Initialize knowledge base
    kb = PyNextKnowledge()
    
    # Build index (first time or after updates)
    await kb.build_index()
    
    # Search for relevant context
    context = kb.search("drag and drop kanban board")
    
    # Get patterns for a feature
    patterns = kb.get_patterns_for("authentication")
    
    # Build optimal context for generation
    prompt_context = kb.build_context(
        task="Create a real-time chat component",
        max_tokens=8000,
    )
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .indexer import KnowledgeIndexer, IndexedChunk
from .retriever import SemanticRetriever, RetrievalResult
from .patterns import PatternLibrary, Pattern
from .embeddings import EmbeddingProvider
from .context_builder import ContextBuilder


@dataclass
class PyNextKnowledge:
    """
    Central knowledge base for PyNext patterns and documentation.
    
    This is the main entry point for the RAG system that powers
    the AI App Builder. It combines:
    - Document/code indexing
    - Semantic search
    - Pattern library
    - Context building
    
    Attributes:
        indexer: Indexes PyNext docs and source code
        retriever: Semantic search over indexed content
        patterns: Library of reusable PyNext patterns
        context_builder: Builds optimal prompts for AI
        cache_dir: Directory for cached embeddings/indices
    
    Example:
        kb = PyNextKnowledge()
        
        # First time setup
        await kb.build_index()
        
        # Search for context
        results = kb.search("websocket real-time updates")
        
        # Build AI prompt context
        context = kb.build_context("Add live chat feature")
    """
    cache_dir: Path = field(default_factory=lambda: Path(__file__).parent / "cache")
    embedding_model: str = "local"
    
    def __post_init__(self):
        """Initialize components."""
        self.embeddings = EmbeddingProvider.create(self.embedding_model)
        self.indexer = KnowledgeIndexer(
            cache_dir=self.cache_dir,
            embeddings=self.embeddings,
        )
        self.retriever = SemanticRetriever(
            indexer=self.indexer,
            embeddings=self.embeddings,
        )
        self.patterns = PatternLibrary()
        self.context_builder = ContextBuilder(
            retriever=self.retriever,
            patterns=self.patterns,
        )
        self._indexed = False
    
    async def build_index(self, force: bool = False) -> None:
        """
        Build the knowledge index.
        
        This indexes all PyNext documentation and source code,
        creating embeddings for semantic search.
        
        Args:
            force: Rebuild even if cache exists
        """
        if self._indexed and not force:
            return
            
        await self.indexer.index_all(force=force)
        self._indexed = True
    
    def load_index(self) -> bool:
        """
        Load index from cache.
        
        Returns:
            True if loaded successfully, False if no cache
        """
        loaded = self.indexer.load_from_cache()
        self._indexed = loaded
        return loaded
    
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
            filters: Filter by chunk_type, source, etc.
        
        Returns:
            List of relevant chunks ranked by relevance
        """
        return self.retriever.search(query, top_k=top_k, filters=filters)
    
    def search_for_feature(self, feature: str) -> Dict[str, Any]:
        """
        Search for everything needed to implement a feature.
        
        Args:
            feature: Feature description
        
        Returns:
            Dict with docs, examples, imports, api_signatures, patterns
        """
        return self.retriever.search_for_feature(feature)
    
    def get_patterns_for(self, feature: str) -> List[Pattern]:
        """
        Get relevant patterns for a feature.
        
        Args:
            feature: Feature name or description
        
        Returns:
            List of applicable patterns
        """
        return self.patterns.get_patterns_for(feature)
    
    def build_context(
        self,
        task: str,
        max_tokens: int = 8000,
        include_patterns: bool = True,
        include_examples: bool = True,
    ) -> str:
        """
        Build optimal context for AI generation.
        
        Args:
            task: The generation task description
            max_tokens: Maximum tokens for context
            include_patterns: Include pattern templates
            include_examples: Include code examples
        
        Returns:
            Formatted context string for AI prompt
        """
        return self.context_builder.build_context(
            task=task,
            max_tokens=max_tokens,
            include_patterns=include_patterns,
            include_examples=include_examples,
        )
    
    def build_file_context(
        self,
        file_type: str,
        requirements: Dict[str, Any],
        existing_files: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Build context for generating a specific file.
        
        Args:
            file_type: Type of file (page, component, api, etc.)
            requirements: File requirements
            existing_files: Already generated files for imports
        
        Returns:
            Formatted context for the specific file
        """
        return self.context_builder.build_file_context(
            file_type=file_type,
            requirements=requirements,
            existing_files=existing_files or {},
        )


# Singleton instance for convenience
_knowledge_instance: Optional[PyNextKnowledge] = None


def get_knowledge() -> PyNextKnowledge:
    """Get or create the global knowledge base instance."""
    global _knowledge_instance
    if _knowledge_instance is None:
        _knowledge_instance = PyNextKnowledge()
    return _knowledge_instance


async def init_knowledge(force_rebuild: bool = False) -> PyNextKnowledge:
    """
    Initialize the knowledge base, building index if needed.
    
    Args:
        force_rebuild: Force rebuild the index
    
    Returns:
        Initialized PyNextKnowledge instance
    """
    kb = get_knowledge()
    
    # Try to load from cache first
    if not force_rebuild and kb.load_index():
        return kb
    
    # Build index
    await kb.build_index(force=force_rebuild)
    return kb


__all__ = [
    "PyNextKnowledge",
    "KnowledgeIndexer",
    "IndexedChunk",
    "SemanticRetriever",
    "RetrievalResult",
    "PatternLibrary",
    "Pattern",
    "EmbeddingProvider",
    "ContextBuilder",
    "get_knowledge",
    "init_knowledge",
]

