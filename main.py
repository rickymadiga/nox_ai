import os
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent

# Try to load .env from project root
env_path = PROJECT_ROOT / ".env"

if env_path.exists():
    print(f"[STARTUP] Loading .env from: {env_path}")
    load_dotenv(env_path, override=True)
else:
    print(f"[STARTUP] ⚠️ .env file not found at: {env_path}")
    # Try current directory
    load_dotenv(override=True)

# Verify key environment variables are loaded
tavily_key = os.getenv("TAVILY_API_KEY", "")
groq_key = os.getenv("GROQ_API_KEY", "")
db_url = os.getenv("DATABASE_URL", "")

print(f"[STARTUP] TAVILY_API_KEY loaded: {bool(tavily_key)}")
print(f"[STARTUP] TAVILY preview: {tavily_key[:30] if tavily_key else 'NOT FOUND'}...")
print(f"[STARTUP] GROQ_API_KEY loaded: {bool(groq_key)}")
print(f"[STARTUP] DATABASE_URL loaded: {bool(db_url)}")
print(f"[STARTUP] Database: {db_url[:50] if db_url else 'NOT FOUND'}...")


import asyncio
import sys
import traceback
from typing import Any, List, Optional, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from nox_backend.models.user import User
from nox_backend.core.database import engine as db_engine, Base

from nox.core.engine import Engine
from nox.core.registry import Registry
from nox.core.event_bus import EventBus
from nox.core.plugin_manager import PluginManager
from nox.core.memory import Memory

from nox.runtime.async_runtime import AsyncRuntimeLoop
from nox.runtime.engine_runtime import engine as runtime_engine  # ✅ Import the global engine
from nox.worlds.world_manager import WorldManager
from nox.worlds.world_runtime import WorldRuntime

from nox.economy.ledger import IntelligenceLedger
from nox.economy.cost_model import CostModel
from nox.runtime.economy_gate import EconomyGate

from nox.utils.logger import logger, setup_logger
from nox.core.routes import router as http_router
from nox_backend.routes.websocket import router as websocket_router
from nox_backend.routes.auth import router as auth_router
from nox_backend.routes.chat import router as chat_router
from nox_backend.routes.builds import router as builds_router
from nox_backend.routes.credits import router as credits_router
from nox_backend.routes.users import router as users_router
from nox_backend.routes.logs import router as logs_router
from nox_backend.routes.forge_stats import router as forge_stats_router
from nox_backend.routes.paystack_callback import router as paystack_callback_router
from nox_backend.routes.paystack import router as paystack_router
from nox_backend.routes.editor import router as editor_router
from nox_backend.routes.video import router as video_router
from nox_backend.routes.research import router as research_router

# ─────────────────────────────────────────────────────────────
# Database Setup
# ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=db_engine)
BASE_DIR = Path(__file__).resolve().parent

# ─────────────────────────────────────────────────────────────
# Database Initialization Function
# ─────────────────────────────────────────────────────────────
def init_database():
    logger.info("🚀 Initializing database schema...")

    from nox_backend.models.user import User

    # Create ORM tables
    Base.metadata.create_all(bind=db_engine)
    logger.info("✅ SQLAlchemy tables created")

    # Create auxiliary tables
    with db_engine.begin() as conn:
        logger.info("🔧 Creating auxiliary tables...")

        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS reset_tokens (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                expires REAL NOT NULL
            )
        """)

        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS payments (
                reference TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                credits INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS builds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_name TEXT,
                status TEXT DEFAULT 'pending',
                size INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_builds_user ON builds(user_id)")
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_builds_status ON builds(status)")
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_builds_created_at ON builds(created_at)")

        logger.info("✅ Auxiliary tables ready")

    # Schema sanity check
    with db_engine.connect() as conn:
        tables = [
            row[0]
            for row in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]

        logger.info(f"📦 Tables in DB: {tables}")

        if "users" not in tables:
            logger.error("❌ 'users' table missing")
            return

        columns = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
        col_names = [col[1] for col in columns]

        logger.info(f"👤 Users columns: {col_names}")

        required = ["id", "username", "email", "password"]
        missing = [col for col in required if col not in col_names]

        if missing:
            logger.error(f"❌ Missing columns: {missing}")
        else:
            logger.info("🎉 Users table schema is correct")

    logger.info("✅ Database initialization complete")


# ─────────────────────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────────────────────
def setup_logging_once() -> None:
    setup_logger()


# ─────────────────────────────────────────────────────────────
# Runtime Shutdown
# ─────────────────────────────────────────────────────────────
async def stop_runtimes(runtimes: Optional[List[Any]]) -> None:
    if not runtimes:
        return

    logger.info("Stopping runtimes...")

    tasks = [
        asyncio.create_task(runtime.stop())
        for runtime in runtimes
        if hasattr(runtime, "stop") and callable(runtime.stop)
    ]

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error("Runtime stop error", exc_info=result)

    logger.info("All runtimes stopped.")


async def graceful_shutdown(
    runtimes: Optional[List[Any]] = None,
    server: Optional[Server] = None,
) -> None:

    logger.info("🛑 Shutdown signal received.")

    await stop_runtimes(runtimes)

    if server and not server.should_exit:
        logger.info("Signaling uvicorn to shutdown...")
        server.should_exit = True


async def bootstrap_system() -> Tuple[Any, Registry, List[Any], Memory]:

    logger.info("🌌 Bootstrapping NOX Core...")

    # ─────────────────────────────
    # DB FIRST (keep this)
    # ─────────────────────────────
    init_database()

    # ─────────────────────────────
    # CORE SYSTEM
    # ─────────────────────────────
    registry = Registry()
    event_bus = EventBus()
    memory = Memory()

    # ─────────────────────────────
    # ECONOMY
    # ─────────────────────────────
    ledger = IntelligenceLedger()
    ledger.create_account("default")

    cost_model = CostModel()
    economy_gate = EconomyGate(ledger, cost_model)

    # ─────────────────────────────
    # ENGINE (FORCE CONSISTENCY)
    # ─────────────────────────────
    engine = runtime_engine
    engine.registry = registry
    engine.event_bus = event_bus

    # 🔴 HARD BIND EVERYTHING (no assumptions)
    engine.event_bus = event_bus
    engine.registry = registry
    engine.memory = memory
    engine.economy_gate = economy_gate

    # ─────────────────────────────
    # PLUGINS (NON-BLOCKING SAFE INIT)
    # ─────────────────────────────
    from nox.core.plugin_manager import PluginManager, load_flat_plugins

    # Class-based plugins → use registry
    plugin_manager = PluginManager(registry)
    plugin_manager.load_plugins()

    # Flat plugins → MUST use engine (runtime!)
    load_flat_plugins(engine)

    logger.info(f"🔌 Loaded {len(plugin_manager.plugins)} plugins")

    async def safe_initialize(plugin):

        if not hasattr(plugin, "initialize"):
            return

        try:
            # ⚡ run in thread → prevents event loop freeze
            await asyncio.to_thread(
                plugin.initialize,
                engine=engine,
                registry=registry,
                event_bus=event_bus,
                memory=memory,
            )

            logger.info(f"✅ Plugin initialized: {plugin.name}")

        except Exception:
            logger.error(
                f"❌ Plugin initialization failed: {plugin.name}",
                exc_info=True
            )

    # Run ALL plugin inits concurrently
    await asyncio.gather(*[
        safe_initialize(p)
        for p in plugin_manager.plugins.values()
    ])

    # ─────────────────────────────
    # WORLDS
    # ─────────────────────────────
    world_manager = WorldManager()

    for name in ["default", "research_simulation"]:
        world_manager.create_world(name)

    logger.info(f"🌍 Active worlds: {list(world_manager.worlds.keys())}")

    # ─────────────────────────────
    # RUNTIMES (WRAPPED = NO FREEZE)
    # ─────────────────────────────
    async_runtime = AsyncRuntimeLoop(engine)
    world_runtime = WorldRuntime(engine, world_manager)

    async def safe_runtime_start(runtime, name):
        try:
            logger.info(f"▶ Starting {name}")
            await runtime.start()
        except Exception:
            logger.critical(f"💥 {name} crashed", exc_info=True)

    runtimes = [
        lambda: safe_runtime_start(async_runtime, "AsyncRuntime"),
        lambda: safe_runtime_start(world_runtime, "WorldRuntime"),
    ]

    logger.info("✅ Core bootstrap complete")

    return engine, registry, runtimes, memory


# ─────────────────────────────────────────────────────────────
# FASTAPI LIFESPAN (✅ CRITICAL)
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""
    
    logger.info("\n" + "="*70)
    logger.info("🚀 FASTAPI LIFESPAN: STARTUP")
    logger.info("="*70)
    
    try:
        # Bootstrap system
        engine, registry, runtimes, memory = await bootstrap_system()

        logger.info("\n" + "="*70)
        logger.info("📌 INJECTING SERVICES INTO app.state")
        logger.info("="*70)

        # ✅ CRITICAL: Inject engine BEFORE handling requests
        app.state.engine = engine
        app.state.registry = registry
        app.state.runtimes = runtimes
        app.state.memory = memory

        logger.info(f"✅ app.state.engine = {type(engine)}")
        logger.info(f"✅ app.state.registry = {type(registry)}")
        logger.info(f"✅ app.state.memory = {type(memory)}")
        logger.info("="*70 + "\n")

        # Start runtimes
        logger.info("🚀 Starting runtimes...")
        for runtime in runtimes:
            if hasattr(runtime, "start"):
                await runtime.start()
        
        logger.info("✅ All runtimes started\n")

    except Exception as e:
        logger.error(f"❌ Startup error: {e}", exc_info=True)
        raise

    # Serve
    yield

    # SHUTDOWN
    logger.info("\n" + "="*70)
    logger.info("🛑 FASTAPI LIFESPAN: SHUTDOWN")
    logger.info("="*70)
    
    await stop_runtimes(runtimes)
    
    logger.info("="*70 + "\n")


# ─────────────────────────────────────────────────────────────
# FASTAPI APP (with lifespan)
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="NOX Backend API",
    description="Core API for NOX AI System",
    version="1.0.0",
    lifespan=lifespan  # ✅ Use lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Register Routers (with /api prefix)
# ─────────────────────────────────────────────────────────────
logger.info("📡 Registering routers with /api prefix...")

app.include_router(http_router, prefix="/api/http", tags=["HTTP"])
app.include_router(websocket_router, prefix="/api/websocket", tags=["websocket"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(builds_router, prefix="/api/builds", tags=["Builds"])
app.include_router(credits_router, prefix="/api/credits", tags=["Credits"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(logs_router, prefix="/api/logs", tags=["Logs"])
app.include_router(forge_stats_router, prefix="/api/forge-stats", tags=["Forge Stats"])
app.include_router(paystack_callback_router, prefix="/api/paystack/callback", tags=["Paystack"])
app.include_router(paystack_router, prefix="/api/paystack", tags=["Paystack"])
app.include_router(editor_router, prefix="/api/editor", tags=["Editor"])
app.include_router(video_router, prefix="/api/video", tags=["Video"])
app.include_router(research_router, prefix="/api/research", tags=["Research"])

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

logger.info("✅ All routers registered\n")

# ─────────────────────────────────────────────────────────────
# Basic Routes
# ─────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "NOX backend running",
        "api_prefix": "/api"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    engine_ready = hasattr(app.state, 'engine') and app.state.engine is not None

    return {
        "status": "healthy" if engine_ready else "degraded",
        "engine_ready": engine_ready,
        "engine_type": str(type(app.state.engine)) if engine_ready else "None",
        "api_prefix": "/api",
        "endpoints": {
            "auth": "/api/auth/login",
            "chat": "/api/chat/message",
            "builds": "/api/builds",
            "downloads": "/api/downloads",
        }
    }


# ─────────────────────────────────────────────────────────────
# Main Runner (for manual execution)
# ─────────────────────────────────────────────────────────────
async def run_server() -> None:
    """Run the server manually"""
    
    setup_logging_once()

    logger.info("\n" + "="*70)
    logger.info("🚀 NOX Core + FastAPI Server Starting")
    logger.info("="*70)
    logger.info("📍 URL: http://0.0.0.0:8000")
    logger.info("📚 Docs: http://0.0.0.0:8000/docs")
    logger.info("="*70 + "\n")

    config = Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        loop="asyncio",
    )

    server = Server(config=config)

    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("⌨️ KeyboardInterrupt received")
    except Exception as e:
        logger.error(f"❌ Server error: {e}", exc_info=True)
        raise


# ─────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────
def main() -> None:
    try:
        setup_logging_once()
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("✅ Shutdown complete.")
    except Exception as e:
        logger.critical("💥 Unhandled exception", exc_info=True)
        print("\n" + "═" * 80)
        print("❌ Unhandled top-level exception")
        print(traceback.format_exc())
        print("═" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()