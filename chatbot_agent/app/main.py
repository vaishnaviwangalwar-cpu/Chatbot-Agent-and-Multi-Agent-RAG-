from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.chat_router import router as chat_router
from app.config import settings

# Create FastAPI application
app = FastAPI(
    title="DY Patil AI Workshop — Project 1 (ChatBot Agent)",
    description="Production-grade AI ChatBot Agent built with Gemini 3.x, FastAPI, Prompt Engineering, Session Memory, and Tool Calling.",
    version="1.0.0",
)

# Enable CORS for cross-origin requests during testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router under /api
app.include_router(chat_router)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "app_env": settings.app_env,
        "model": settings.gemini_model,
        "api_key_configured": bool(settings.gemini_api_key),
    }


# Mount static assets for Web UI (must be last)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.app_env == "development"),
    )
