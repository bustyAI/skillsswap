from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from app.recommender.embeddings import EMBEDDING_DIM, encode

router = APIRouter(prefix="/debug", tags=["debug"])
security = HTTPBearer(auto_error=False)


@router.get("/embed")
def get_embedding(text: str = Query(..., min_length=1)) -> dict[str, object]:
    """Return the embedding vector for the given text."""
    embedding = encode(text)
    return {
        "text": text,
        "embedding": embedding,
        "dimensions": EMBEDDING_DIM,
    }


@router.get("/token-claims")
def get_token_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> dict[str, object]:
    """Decode and return JWT claims without validation (for debugging)."""
    if not credentials:
        return {"error": "No token provided"}
    token = credentials.credentials
    try:
        claims = jwt.get_unverified_claims(token)
        return {"claims": claims}
    except Exception as e:
        return {"error": str(e)}
