from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from prometheus_client import make_asgi_app
from config import settings
from src.api.routes import router
from src.monitoring.metrics import APP_INFO, COLD_STARTS
from src.utils.logging import get_logger
import os

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    APP_INFO.info({"version": "1.0.0", "environment": settings.ENVIRONMENT})
    COLD_STARTS.inc()
    logger.info(f"Ledgera started in {settings.ENVIRONMENT} mode")
    yield


app = FastAPI(
    title="Ledgera - Multimodal Agentic Book Reviewer",
    version="1.0.0",
    description="AI-powered book analysis from cover images",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
async def serve_frontend():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Ledgera API is running. Frontend not found."}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
