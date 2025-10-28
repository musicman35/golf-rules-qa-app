"""
Embeddings module for RAG system.
Supports Voyage AI and local sentence-transformers for vector embeddings.
"""

import os
from typing import List, Optional, Dict
import numpy as np
from loguru import logger

# Import embedding libraries
try:
    import voyageai
    VOYAGE_AVAILABLE = True
except ImportError:
    VOYAGE_AVAILABLE = False
    logger.warning("VoyageAI not available, will use local embeddings")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available")


class EmbeddingService:
    """
    Service for generating text embeddings using various providers.
    Supports both API-based (Voyage) and local (sentence-transformers) models.
    """

    def __init__(self, provider: str = "voyage", model_name: Optional[str] = None):
        """
        Initialize embedding service.

        Args:
            provider: 'voyage' or 'local'
            model_name: Specific model name (optional)
        """
        self.provider = provider.lower()
        self.model_name = model_name
        self.client = None
        self.model = None

        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the embedding provider."""
        if self.provider == "voyage":
            if not VOYAGE_AVAILABLE:
                logger.warning("Voyage not available, falling back to local")
                self.provider = "local"
                self._initialize_local()
            else:
                self._initialize_voyage()
        elif self.provider == "local":
            self._initialize_local()
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _initialize_voyage(self):
        """Initialize Voyage AI client."""
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            logger.warning("VOYAGE_API_KEY not found, falling back to local")
            self.provider = "local"
            self._initialize_local()
            return

        try:
            self.client = voyageai.Client(api_key=api_key)
            self.model_name = self.model_name or "voyage-2"
            logger.info(f"Initialized Voyage AI with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Voyage AI: {e}")
            logger.warning("Falling back to local embeddings")
            self.provider = "local"
            self._initialize_local()

    def _initialize_local(self):
        """Initialize local sentence-transformers model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "No embedding provider available. Install voyageai or sentence-transformers"
            )

        try:
            # Use a good all-around model
            self.model_name = self.model_name or "all-MiniLM-L6-v2"
            logger.info(f"Loading local embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Initialized local embeddings with {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize local embeddings: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            if self.provider == "voyage":
                return self._embed_voyage(texts)
            else:
                return self._embed_local(texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def _embed_voyage(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Voyage AI."""
        try:
            result = self.client.embed(
                texts,
                model=self.model_name,
                input_type="document"  # For indexing documents
            )
            embeddings = result.embeddings

            logger.info(f"Generated {len(embeddings)} embeddings via Voyage AI")
            return embeddings

        except Exception as e:
            logger.error(f"Voyage embedding failed: {e}")
            raise

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local sentence-transformers."""
        try:
            # Convert to list format
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10
            )

            # Convert numpy arrays to lists
            embeddings = embeddings.tolist()

            logger.info(f"Generated {len(embeddings)} embeddings via local model")
            return embeddings

        except Exception as e:
            logger.error(f"Local embedding failed: {e}")
            raise

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        try:
            if self.provider == "voyage":
                # Use query input type for Voyage
                result = self.client.embed(
                    [query],
                    model=self.model_name,
                    input_type="query"
                )
                return result.embeddings[0]
            else:
                # Local model
                embedding = self.model.encode([query], convert_to_numpy=True)
                return embedding[0].tolist()

        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    def get_embedding_dim(self) -> int:
        """Get the dimensionality of the embeddings."""
        if self.provider == "voyage":
            # Voyage-2 has 1024 dimensions
            return 1024
        else:
            # Get from model
            return self.model.get_sentence_embedding_dimension()


# Singleton instance
_embedding_service = None


def get_embedding_service(provider: str = None) -> EmbeddingService:
    """
    Get or create singleton embedding service.

    Args:
        provider: 'voyage' or 'local' (defaults to environment variable or 'local')

    Returns:
        EmbeddingService instance
    """
    global _embedding_service

    if _embedding_service is None:
        if provider is None:
            # Check environment variable
            embedding_model = os.getenv("EMBEDDING_MODEL", "local")
            if "voyage" in embedding_model.lower():
                provider = "voyage"
            else:
                provider = "local"

        _embedding_service = EmbeddingService(provider=provider)

    return _embedding_service


if __name__ == "__main__":
    # Test the embedding service
    service = get_embedding_service("local")

    # Test texts
    texts = [
        "What is the penalty for hitting a ball out of bounds?",
        "The penalty for out of bounds is stroke and distance.",
        "How do I repair a ball mark on the green?"
    ]

    # Generate embeddings
    embeddings = service.embed_texts(texts)
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")

    # Test similarity
    query_embedding = service.embed_query("What happens if my ball goes OB?")
    similarity_1 = service.cosine_similarity(query_embedding, embeddings[0])
    similarity_2 = service.cosine_similarity(query_embedding, embeddings[1])

    print(f"\nQuery similarity to text 1: {similarity_1:.3f}")
    print(f"Query similarity to text 2: {similarity_2:.3f}")
