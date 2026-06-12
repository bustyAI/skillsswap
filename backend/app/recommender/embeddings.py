"""
Embedding generation using sentence-transformers/all-MiniLM-L6-v2.

Memory footprint:
- Model weights: ~90MB on disk, ~400MB in RAM when loaded
- Inference: negligible additional RAM per request

The model is loaded lazily on first use and cached globally.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model: "SentenceTransformer | None" = None


def get_embedding_model() -> "SentenceTransformer":
    """Return the singleton embedding model, loading it if necessary."""
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", MODEL_NAME)
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully")
    return _model


def encode(text: str) -> list[float]:
    """Encode text into a 384-dimensional embedding vector."""
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()  # type: ignore[no-any-return]
