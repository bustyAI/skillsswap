import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api.admin import router as admin_router
from app.api.health import router as health_router
from app.api.me import router as me_router
from app.api.meetings import router as meetings_router
from app.api.mentors import router as mentors_router
from app.api.mentorships import router as mentorships_router
from app.api.reports import router as reports_router
from app.api.topics import router as topics_router
from app.api.users import router as users_router
from app.recommender.embeddings import get_embedding_model

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up: loading embedding model")
    get_embedding_model()
    logger.info("Embedding model ready")
    yield


app = FastAPI(
    title="SkillSwap API",
    description="Mentorship platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# Parent router for all API routes - add new routers here
api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(me_router)
api_router.include_router(meetings_router)
api_router.include_router(mentors_router)
api_router.include_router(mentorships_router)
api_router.include_router(reports_router)
api_router.include_router(topics_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)

app.include_router(api_router)
