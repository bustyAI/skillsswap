from fastapi import APIRouter, FastAPI

from app.api.health import router as health_router
from app.api.me import router as me_router

app = FastAPI(
    title="SkillSwap API",
    description="Mentorship platform API",
    version="0.1.0",
)

# Parent router for all API routes - add new routers here
api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(me_router)

app.include_router(api_router)
