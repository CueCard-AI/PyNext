"""
Embedding Provider - Generates vector embeddings for semantic search.

Supports:
- Local embeddings (sentence-transformers) - No API needed
- Anthropic embeddings (via API)
- OpenAI embeddings (via API)

Example:
    # Local embeddings (default, no API key needed)
    provider = EmbeddingProvider.create("local")
    
    # Single embedding
    vector = await provider.embed("Search query")
    
    # Batch embedding
    vectors = await provider.embed_batch(["text1", "text2"])
"""

import asyncio
import hashlib
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    
    Embeddings are vector representations of text that enable
    semantic similarity search.
    """
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Vector embedding as list of floats
        """
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of vector embeddings
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimension of the embedding vectors."""
        pass
    
    @staticmethod
    def create(
        model: str = "local",
        api_key: Optional[str] = None,
    ) -> "EmbeddingProvider":
        """
        Create an embedding provider.
        
        Args:
            model: Provider type - "local", "anthropic", "openai"
            api_key: API key for cloud providers
        
        Returns:
            EmbeddingProvider instance
        """
        if model == "local":
            return LocalEmbeddingProvider()
        elif model == "anthropic":
            return AnthropicEmbeddingProvider(api_key=api_key)
        elif model == "openai":
            return OpenAIEmbeddingProvider(api_key=api_key)
        else:
            logger.warning(f"Unknown embedding model {model}, using local")
            return LocalEmbeddingProvider()


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local embeddings using sentence-transformers.
    
    Uses all-MiniLM-L6-v2 by default (fast, 384 dimensions).
    No API key needed - runs entirely locally.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embedding provider.
        
        Args:
            model_name: Sentence transformer model name
        """
        self.model_name = model_name
        self._model = None
        self._dimension = 384  # Default for MiniLM
    
    def _get_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed. "
                    "Using fallback hash-based embeddings. "
                    "Install with: pip install sentence-transformers"
                )
                self._model = "fallback"
        return self._model
    
    @property
    def dimension(self) -> int:
        """Dimension of embeddings."""
        return self._dimension
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        model = self._get_model()
        
        if model == "fallback":
            return self._fallback_embed(text)
        
        # Run in thread pool to not block
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(text, convert_to_numpy=True).tolist()
        )
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        model = self._get_model()
        
        if model == "fallback":
            return [self._fallback_embed(t) for t in texts]
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(texts, convert_to_numpy=True).tolist()
        )
        return embeddings
    
    def _fallback_embed(self, text: str) -> List[float]:
        """
        Fallback embedding using hash-based approach.
        
        This is NOT semantic but allows the system to work
        without sentence-transformers installed.
        """
        # Create a deterministic hash-based embedding
        hash_bytes = hashlib.sha384(text.encode()).digest()
        # Convert to floats in [-1, 1]
        embedding = [(b / 127.5) - 1.0 for b in hash_bytes]
        return embedding


class AnthropicEmbeddingProvider(EmbeddingProvider):
    """
    Embeddings using Anthropic's API.
    
    Note: As of 2024, Anthropic doesn't have a dedicated embedding API,
    so this uses a text-based approach with Claude.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Anthropic embedding provider.
        
        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._dimension = 1024  # Simulated dimension
        
        # Since Anthropic doesn't have embeddings, we fall back to local
        logger.info(
            "Anthropic doesn't have a native embedding API. "
            "Using local embeddings instead."
        )
        self._fallback = LocalEmbeddingProvider()
    
    @property
    def dimension(self) -> int:
        return self._fallback.dimension
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using fallback."""
        return await self._fallback.embed(text)
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using fallback."""
        return await self._fallback.embed_batch(texts)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Embeddings using OpenAI's API.
    
    Uses text-embedding-3-small by default (1536 dimensions).
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
    ):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env)
            model: OpenAI embedding model name
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self._dimension = 1536 if "small" in model else 3072
        self._client = None
    
    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )
        return self._client
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        client = self._get_client()
        response = await client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        
        client = self._get_client()
        
        # OpenAI has a limit on batch size, process in chunks
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await client.embeddings.create(
                model=self.model,
                input=batch,
            )
            all_embeddings.extend([d.embedding for d in response.data])
        
        return all_embeddings


class CachedEmbeddingProvider(EmbeddingProvider):
    """
    Wrapper that caches embeddings to disk.
    
    Useful for development to avoid re-computing embeddings.
    """
    
    def __init__(
        self,
        provider: EmbeddingProvider,
        cache_dir: Optional[Path] = None,
    ):
        """
        Initialize cached provider.
        
        Args:
            provider: Underlying embedding provider
            cache_dir: Directory for cache
        """
        self.provider = provider
        self.cache_dir = cache_dir or Path(__file__).parent / "cache" / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[float]] = {}
        self._load_cache()
    
    def _cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.sha256(text.encode()).hexdigest()[:32]
    
    def _load_cache(self):
        """Load cache from disk."""
        cache_file = self.cache_dir / "embedding_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        cache_file = self.cache_dir / "embedding_cache.json"
        with open(cache_file, "w") as f:
            json.dump(self._cache, f)
    
    @property
    def dimension(self) -> int:
        return self.provider.dimension
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding with caching."""
        key = self._cache_key(text)
        
        if key in self._cache:
            return self._cache[key]
        
        embedding = await self.provider.embed(text)
        self._cache[key] = embedding
        self._save_cache()
        
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with caching."""
        results = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            key = self._cache_key(text)
            if key in self._cache:
                results.append(self._cache[key])
            else:
                results.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Embed uncached texts
        if uncached_texts:
            new_embeddings = await self.provider.embed_batch(uncached_texts)
            
            # Update results and cache
            for idx, embedding, text in zip(uncached_indices, new_embeddings, uncached_texts):
                results[idx] = embedding
                self._cache[self._cache_key(text)] = embedding
            
            self._save_cache()
        
        return results

