from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routers.admin_users import router as admin_users_router
from app.api.routers.auth import router as auth_router
from app.api.routers.claims import router as claims_router
from app.api.routers.communication import router as communication_router
from app.api.routers.customer_management import router as customer_management_router
from app.api.routers.health import router as health_router
from app.api.routers.insurance import router as insurance_router
from app.api.routers.rag import router as rag_router
from app.api.routers.subscriptions import router as subscriptions_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_users_router)
    app.include_router(insurance_router)
    app.include_router(customer_management_router)
    app.include_router(subscriptions_router)
    app.include_router(claims_router)
    app.include_router(communication_router)
    app.include_router(rag_router)

    claim_upload_dir = Path(settings.CLAIM_UPLOAD_DIR)
    claim_upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/uploads/claims",
        StaticFiles(directory=claim_upload_dir),
        name="claim_uploads",
    )

    return app


app = create_app()
