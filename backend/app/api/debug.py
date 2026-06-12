from fastapi import APIRouter, Query

from app.recommender.embeddings import EMBEDDING_DIM, encode

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/embed")
def get_embedding(text: str = Query(..., min_length=1)) -> dict[str, object]:
    """Return the embedding vector for the given text."""
    embedding = encode(text)
    return {
        "text": text,
        "embedding": embedding,
        "dimensions": EMBEDDING_DIM,
    }
