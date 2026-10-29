from fastapi import APIRouter

from oligospace_api.api.routes import auth, dashboard, health, laboratory, registry, workspace

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(registry.router)
api_router.include_router(laboratory.router)
api_router.include_router(workspace.router)
