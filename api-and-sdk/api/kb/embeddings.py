"""
Embedding service for vector-based retrieval.

Uses all-MiniLM-L6-v2 (fast, lightweight, good for semantic search).
Falls back to BAAI/bge-small-en-v1.5 if available.
Model is cached at module level to avoid reloading.

Runnable: from api.kb.embeddings import embed_texts
"""

import os
import numpy as np
import warnings

warnings.filterwarnings('ignore')

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "sentence-transformers not installed. Run: pip install sentence-transformers"
    )

# Cache the model at module level
_model = None


def get_model():
    """Load and cache the embedding model."""
    global _model
    if _model is None:
        # Disable SSL verification for model download
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        
        import ssl
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
        except:
            pass
        
        # Try loading preferred model first, fall back to simpler model
        models_to_try = [
            "all-MiniLM-L6-v2",  # Smaller, usually already cached
            "BAAI/bge-small-en-v1.5",  # Preferred but larger
        ]
        
        for model_name in models_to_try:
            try:
                print(f"Loading embedding model: {model_name}...")
                _model = SentenceTransformer(model_name, device="cpu")
                print(f"✓ Model loaded: {model_name} ({_model.get_sentence_embedding_dimension()} dims)")
                return _model
            except Exception as e:
                print(f"  ✗ Failed to load {model_name}: {type(e).__name__}")
                continue
        
        # If all models fail, raise error
        raise RuntimeError(
            "Could not load any embedding model. "
            "Please ensure internet connection is available or pre-download the model."
        )
    
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Embed a list of texts using the cached model.

    Args:
        texts: List of strings to embed

    Returns:
        numpy array of shape (len(texts), 384)
        Normalized so cosine similarity = inner product
    """
    if not texts:
        return np.array([])

    model = get_model()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,  # Critical for cosine similarity via inner product
        show_progress_bar=False,
    )
    return embeddings


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.

    Args:
        query: Query text

    Returns:
        1D numpy array of shape (384,), normalized
    """
    embedding = embed_texts([query])
    return embedding[0]  # Return 1D array
