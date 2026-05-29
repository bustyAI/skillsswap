from fastapi import APIRouter, FastAPI

from app.api.health import router as health_router
from app.api.me import router as me_router
from app.api.mentors import router as mentors_router
from app.api.topics import router as topics_router
from app.api.users import router as users_router

app = FastAPI(
    title="SkillSwap API",
    description="Mentorship platform API",
    version="0.1.0",
)

# Parent router for all API routes - add new routers here
api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(me_router)
api_router.include_router(mentors_router)
api_router.include_router(topics_router)
api_router.include_router(users_router)

app.include_router(api_router)
