import os
import json
from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

# ====================== IMPORTS ======================
from nox_backend.core.database import engine, init_db

# ✅ CRITICAL: Import the runtime engine
try:
    from nox.runtime.engine_runtime import engine as runtime_engine
    print("✅ Successfully imported runtime_engine")
except ImportError as e:
    print(f"❌ Failed to import runtime_engine: {e}")
    runtime_engine = None

from nox_backend.routes.auth import router as auth_router
from nox_backend.routes import websocket
from nox_backend.routes import chat, admin, video, research
from nox_backend.routes import paystack, forge_stats, credits, logs, paystack_callback, user, download, builds, editor

from nox_backend.core import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# ====================== LIFESPAN ======================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    print("\n" + "="*60)
    print("🚀 NOX Backend STARTING...")
    print("="*60)
    
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database init failed: {e}")
    
    if runtime_engine is not None:
        app.state.engine = runtime_engine
        print(f"✅ Runtime engine initialized: {type(runtime_engine)}")
    else:
        print("❌ Runtime engine is None!")
        app.state.engine = None
    
    print("="*60)
    print("✅ Startup complete\n")
    
    yield
    
    print("\n" + "="*60)
    print("🛑 NOX Backend SHUTTING DOWN...")
    print("="*60)

# ====================== APP ======================
app = FastAPI(
    title="NOX Backend API",
    description="Backend API for NOX AI",
    version="1.0.0",
    lifespan=lifespan
)

# ====================== RATE LIMITER ======================
rate_limiter = Limiter(key_func=get_remote_address)
app.state.limiter = rate_limiter

# ====================== MIDDLEWARE ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== ROUTERS ======================
print("📡 Registering routers...")

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(websocket.router, prefix="/api/websocket", tags=["WebSocket"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(paystack.router, prefix="/api/paystack", tags=["Paystack"])
app.include_router(forge_stats.router, prefix="/api/forge-stats", tags=["Forge Stats"])
app.include_router(credits.router, prefix="/api/credits", tags=["Credits"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(paystack_callback.router, prefix="/api/paystack-callback", tags=["Paystack Callback"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(download.router, prefix="/api/download", tags=["Download"])
app.include_router(builds.router, prefix="/api/builds", tags=["Builds"])
app.include_router(editor.router, prefix="/api/editor", tags=["Editor"])
app.include_router(video.router, prefix="/api/video", tags=["Video"])

print("✅ All routers registered with /api prefix\n")

# ====================== STATIC FILES ======================
os.makedirs("static/videos", exist_ok=True)
os.makedirs("generated_apps", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/exports", StaticFiles(directory="generated_apps"), name="exports")

# ====================== STREAM ENDPOINT ======================
@app.get("/stream")
async def stream_logs(request: Request):
    """Server-Sent Events for live logs"""
    async def event_generator():
        try:
            for _ in range(30):
                if await request.is_disconnected():
                    break
                await asyncio.sleep(0.8)
            yield {"data": json.dumps({"status": "complete"})}
        except Exception as e:
            logger.error(f"[STREAM] Error: {e}")
            yield {"data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())

# ====================== BASIC ROUTES ======================
@app.get("/")
def root():
    return {
        "status": "NOX Backend is running 🔥",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    engine_ready = hasattr(app.state, 'engine') and app.state.engine is not None
    return {
        "status": "healthy" if engine_ready else "degraded",
        "database": str(engine.url),
        "engine_ready": engine_ready,
        "engine_type": str(type(app.state.engine)) if engine_ready else "None",
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting NOX Backend Server")
    print("="*60)
    print("📍 URL: http://0.0.0.0:8000")
    print("📚 Docs: http://0.0.0.0:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )