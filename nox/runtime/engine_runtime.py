import asyncio
from email import message
import time
import logging
import json
import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)
DEV_USERS = ["nox", "admin", "cosmic ethic"]

try:
    from ...nox.core.ws_manager import ConnectionManager
except ImportError:
    ConnectionManager = (None)  # Placeholder if ws_manager is not available

from ..core.capability_index import CapabilityIndex
from ..core.memory import InMemoryHistoryStore
from .plugin_loader import load_plugins
from ..core.video_jobs import VideoJobManager

# ────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ────────────────────────────────────────────────
def get_utc_timestamp() -> str:
    """Get current UTC timestamp using timezone-aware datetime"""
    return datetime.now(timezone.utc).isoformat()


# ────────────────────────────────────────────────
# SIMPLE EVENT BUS
# ────────────────────────────────────────────────
class SimpleBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.pending_events: Dict[str, List[asyncio.Event]] = defaultdict(list)
        self.all_logs: List[str] = []  # ✅ Fixed: Initialize as list
        self.user_logs: Dict[str, List[str]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type"""
        self.subscribers[event_type].append(callback)
        logger.debug(f"[BUS] Subscribed to event: {event_type}")

    def add_log(self, user_id: str, message: str) -> None:
        """Add a log entry"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        # Store in user logs
        if user_id not in self.user_logs:
            self.user_logs[user_id] = []
        self.user_logs[user_id].append(log_entry)

        # Store in global logs (for admin)
        self.all_logs.append(log_entry)

        logger.debug(f"[RUNTIME] Log added: {message}")

    def get_all_logs(self) -> list:
        """Get all logs (for admin)"""
        return self.all_logs[-1000:]  # Last 1000

    def clear_all_logs(self) -> None:
        """Clear all logs"""
        self.all_logs = []
        self.user_logs = defaultdict(list)
        logger.info("[RUNTIME] All logs cleared")

    def get_logs(self, user_id: str, limit: int = 100) -> list:
        """Get user logs"""
        logs = self.user_logs.get(user_id, [])
        return logs[-limit:] if len(logs) > limit else logs

    async def publish(self, message: Any) -> None:
        """Publish message to subscribers"""
        if isinstance(message, dict):
            event_type = message.get("type") or message.get("message_type")
        elif hasattr(message, "message_type"):
            event_type = message.message_type
        else:
            event_type = None

        if not event_type:
            return

        logger.info(f"[BUS] Publishing event: {event_type}")

        # Signal all waiters FIRST
        for waiter in self.pending_events.get(event_type, []):
            waiter.set()
        self.pending_events[event_type] = []

        # Then call subscribers
        for callback in self.subscribers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"[BUS ERROR] {event_type}: {e}", exc_info=True)

    def create_waiter(self, event_type: str) -> asyncio.Event:
        """Create a waiter for an event"""
        waiter = asyncio.Event()
        self.pending_events[event_type].append(waiter)
        logger.info(f"[BUS] Waiter created for: {event_type}")
        return waiter

    async def wait_for_event(self, event_type: str, timeout: float = 30) -> bool:
        """Wait for an event to be published"""
        waiter = self.create_waiter(event_type)

        try:
            await asyncio.wait_for(waiter.wait(), timeout=timeout)
            logger.info(f"[BUS] Event received: {event_type}")
            return True
        except asyncio.TimeoutError:
            logger.warning(f"[BUS] Timeout waiting for {event_type} (waited {timeout}s)")
            return False


# ────────────────────────────────────────────────
# RUNTIME CORE
# ────────────────────────────────────────────────
class Runtime:
    def __init__(self, bus: Optional[SimpleBus] = None):
        self.bus = bus or SimpleBus()
        self.skills = {}
        self.projects = {}
        self.agents: Dict[str, Any] = {}
        self.system_agents: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
        self.capabilities = CapabilityIndex()
        self.memory = InMemoryHistoryStore()

        self.video_manager = VideoJobManager()

        # ✅ IMPORTANT: Start worker on Windows
        try:
            self.video_manager.start_worker()
            logger.info("[RUNTIME] VideoJobManager worker started")
        except Exception as e:
            logger.error(f"[RUNTIME] Failed to start video worker: {e}", exc_info=True)

        #start ackground worker for video processing
        asyncio.create_task(self.video_manager.worker())

        self.video_manager = VideoJobManager()
        asyncio.create_task(self.video_manager.worker())

        logger.info("[RUNTIME] VideoJobManager initialized and worker started")
        

        # Multi-user support
        self.last_zip: Dict[str, Dict[str, Any]] = {}
        self.user_logs: Dict[str, List[str]] = defaultdict(list)
        self.logs: List[str] = []

        # Pending ZIP data from build
        self.pending_zip: Dict[str, Dict[str, Any]] = {}

        # Live log subscribers for real-time updates
        self.log_subscribers: Dict[str, List[Callable]] = defaultdict(list)

        # Subscribe to forge completion event
        self.bus.subscribe("forge_complete", self._on_forge_complete)
        self.bus.subscribe("CODE_APPROVED", self._on_code_approved)

        self.role_map = {
            "debugger": "code_assistant",
            "fixer": "code_assistant",
            "reviewer": "code_assistant",
            "tester": "code_assistant"
        }

        logger.info("[RUNTIME] Initialized successfully")

    # ───── LOG COLLECTION ─────
    def add_log(self, user_id: str, message: str) -> None:
        """Add a log entry and emit to live subscribers"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        self.user_logs[user_id].append(log_entry)
        self.logs.append(log_entry)

        logger.debug(f"[LOG] {user_id}: {message}")

    async def _emit_live_log(self, user_id: str, log_entry: str) -> None:
        """Emit log to all subscribers for this user"""
        try:
            for callback in self.log_subscribers.get(user_id, []):
                if asyncio.iscoroutinefunction(callback):
                    await callback(log_entry)
                else:
                    callback(log_entry)
        except Exception as e:
            logger.error(f"[LOG EMIT ERROR] {e}", exc_info=True)

    def subscribe_logs(self, user_id: str, callback: Callable) -> None:
        """Subscribe to live logs for a user"""
        self.log_subscribers[user_id].append(callback)
        logger.info(f"[LOG] Subscriber added for {user_id}")

    def get_logs(self, user_id: str, limit: int = 100) -> List[str]:
        """Get recent logs for a user"""
        return self.user_logs[user_id][-limit:]

    def clear_logs(self, user_id: str) -> None:
        """Clear logs for a user"""
        self.user_logs[user_id] = []
        logger.info(f"[LOG] Logs cleared for {user_id}")

    # ───── ZIP HANDLING ─────
    def has_zip_for_user(self, user_id: str) -> bool:
        """Check if user has a downloadable ZIP"""
        return user_id in self.last_zip and self.last_zip[user_id].get("size", 0) > 0

    def set_zip(self, user_id: str, zip_bytes: bytes, filename: str) -> None:
        """Store ZIP for a user"""
        try:
            if isinstance(zip_bytes, str):
                zip_bytes = base64.b64decode(zip_bytes)

            # Ensure zip_bytes is bytes
            if not isinstance(zip_bytes, bytes):
                zip_bytes = str(zip_bytes).encode('utf-8')

            self.last_zip[user_id] = {
                "data": base64.b64encode(zip_bytes).decode('utf-8'),
                "filename": filename,
                "size": len(zip_bytes),
                "created_at": get_utc_timestamp()
            }
            logger.info(f"[ZIP] ✅ Stored {len(zip_bytes)} bytes for {user_id}: {filename}")
        except Exception as e:
            logger.error(f"[ZIP ERROR] Failed to set ZIP: {e}", exc_info=True)

    def get_zip(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get ZIP for a user (ready for frontend transmission)"""
        zip_data = self.last_zip.get(user_id)
        if zip_data:
            size = zip_data.get("size", 0)
            if size == 0 and "data" in zip_data:
                try:
                    decoded = base64.b64decode(zip_data["data"])
                    size = len(decoded)
                except:
                    size = 0

            logger.info(f"[ZIP] ✅ Retrieved {size} bytes for {user_id}")
            return {
                "data": zip_data.get("data", ""),
                "filename": zip_data.get("filename", "nox_app.zip"),
                "size": size,
                "download_url": f"/api/download/{user_id}/{zip_data.get('filename', 'nox_app.zip')}"
            }
        else:
            logger.warning(f"[ZIP] ❌ No ZIP found for {user_id}")
        return None

    def store_pending_zip(self, user_id: str, context: Dict[str, Any]) -> None:
        """Extract and store ZIP from build context"""
        try:
            zip_path = context.get("zip_path")
            filename = context.get("filename") or context.get("project_name", "nox_app.zip")

            if zip_path and filename:
                logger.info(f"[ZIP] Found pending ZIP at: {zip_path}")

                try:
                    import os
                    if os.path.exists(zip_path):
                        with open(zip_path, 'rb') as f:
                            zip_bytes = f.read()
                        self.set_zip(user_id, zip_bytes, filename)
                        self.add_log(user_id, f"✅ ZIP loaded from disk: {filename}")
                        logger.info(f"[ZIP] ✅ Loaded {len(zip_bytes)} bytes from {zip_path}")
                        return
                except Exception as e:
                    logger.error(f"[ZIP] Failed to read from disk: {e}")

            self.add_log(user_id, "⚠️ ZIP not found in context")
        except Exception as e:
            logger.error(f"[ZIP] Error storing pending ZIP: {e}", exc_info=True)

    # ───── EVENT HANDLERS ─────
    async def _on_code_approved(self, message: Any) -> None:
        """Capture build context before forge_complete fires"""
        try:
            logger.info("[RUNTIME] CODE_APPROVED event received - capturing context")

            payload = (
                message.payload
                if hasattr(message, "payload")
                else message.get("payload", {})
            )

            user_id = payload.get("user_id", "guest")
            context = payload.get("context", {})

            if context:
                self.pending_zip[user_id] = context
                logger.info(f"[RUNTIME] Stored pending context for {user_id}")

        except Exception as e:
            logger.error(f"[RUNTIME] Error in _on_code_approved: {e}", exc_info=True)

    async def _on_forge_complete(self, message: Any) -> None:
        """Handle forge completion and extract ZIP"""
        try:
            logger.info("[RUNTIME] forge_complete event received")

            payload = (
                message.payload
                if hasattr(message, "payload")
                else message.get("payload", {})
            )

            user_id = payload.get("user_id", "guest")
            logger.info(f"[FORGE] Processing for user: {user_id}")

            zip_bytes = payload.get("zip_bytes")
            filename = payload.get("filename", "nox_app.zip")

            if not zip_bytes:
                logger.info(f"[FORGE] No zip_bytes in payload, checking pending context")
                context = self.pending_zip.get(user_id, {})
                if context:
                    self.store_pending_zip(user_id, context)
                    zip_bytes = "pending"

            if not zip_bytes:
                logger.info(f"[FORGE] Checking runtime.last_zip")
                existing_zip = self.last_zip.get(user_id)
                if existing_zip:
                    logger.info(f"[FORGE] ✅ Found existing ZIP in runtime")
                    self.add_log(user_id, f"✅ Build complete: {existing_zip['filename']}")
                    return

            if zip_bytes and zip_bytes != "pending":
                self.set_zip(user_id, zip_bytes, filename)
                # Force refresh
                zip_data = self.get_zip(user_id)
                if zip_data:
                    self.add_log(user_id, f"✅ ZIP ready for download: {zip_data['filename']}")

                self.add_log(user_id, f"✅ Build complete: {filename}")
            else:
                self.add_log(user_id, f"✅ Build complete")

            if user_id in self.pending_zip:
                del self.pending_zip[user_id]

            lily = self.get_agent("lily")
            if lily and hasattr(lily, "complete_job"):
                lily.complete_job(user_id, self.get_zip(user_id))

            logger.info(f"[FORGE] ✅ Processed for {user_id}")

        except Exception as e:
            logger.error(f"[RUNTIME] Error in _on_forge_complete: {e}", exc_info=True)

    # ───── TOOLS ─────
    def register_tool(self, name: str, tool: Any) -> None:
        self.tools[name] = tool
        logger.info(f"[TOOL] Registered: {name}")

    def get_tool(self, name: str) -> Optional[Any]:
        return self.tools.get(name)

    # ───── AGENTS ─────
    def register_agent(self, name: str, agent: Any) -> None:
        try:
            if hasattr(agent, "runtime"):
                agent.runtime = self
            self.agents[name] = agent
            logger.info(f"[AGENT] Registered: {name}")
        except Exception as e:
            logger.error(f"[AGENT ERROR] Failed to register {name}: {e}", exc_info=True)

    def register_system_agent(self, name: str, agent: Any) -> None:
        try:
            if hasattr(agent, "runtime"):
                agent.runtime = self
            self.system_agents[name] = agent
            logger.info(f"[SYSTEM AGENT] Registered: {name}")
        except Exception as e:
            logger.error(f"[SYSTEM AGENT ERROR] Failed to register {name}: {e}", exc_info=True)

    def get_agent(self, name: str) -> Optional[Any]:
        real_name = self.role_map.get(name, name)
        return self.agents.get(real_name) or self.system_agents.get(real_name)

    # ───── CAPABILITIES ─────
    def register_capability(
        self,
        agent_name: str,
        intent: str,
        keywords: List[str],
        priority: int = 0
    ) -> None:
        try:
            self.capabilities.register(
                agent_name=agent_name,
                intent=intent,
                keywords=keywords
            )
            if priority != 0:
                self.capabilities.set_priority(agent_name, priority)

            logger.info(f"[CAPABILITY] Registered → {agent_name} for intent: {intent}")
        except Exception as e:
            logger.error(f"[CAPABILITY ERROR] {agent_name}: {e}", exc_info=True)

    # ───── EXECUTION ─────
    async def execute_agent(self, name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        agent = self.get_agent(name)
        if not agent:
            return {"error": f"Agent '{name}' not found"}

        try:
            result = agent.run(task)
            if asyncio.iscoroutine(result):
                result = await result
            return result or {}
        except Exception as e:
            logger.error(f"[AGENT EXECUTION ERROR] {name}: {e}", exc_info=True)
            return {"error": str(e)}


# ────────────────────────────────────────────────
# MAIN ENGINE
# ────────────────────────────────────────────────
class Engine:
    MIN_BUILD_CREDITS = 200

    def __init__(self):
        self.runtime = Runtime()
        self._billing_locks = defaultdict(asyncio.Lock)
        self.runtime.engine = self

        class SimpleEventBus:
            def __init__(self):
                self.listeners = defaultdict(list)

            def subscribe(self, event, callback):
                self.listeners[event].append(callback)

            def emit(self, event, payload):
                for cb in self.listeners.get(event, []):
                    try:
                        cb(payload)
                    except Exception as e:
                        print(f"[EventBus] Listener error: {e}")

        self.event_bus = SimpleEventBus()

        try:
            load_plugins(self.runtime)
            logger.info("[ENGINE] Plugins loaded successfully")
        except Exception as e:
            logger.error(f"[PLUGIN LOAD ERROR] {e}", exc_info=True)

        logger.info("[ENGINE] ✅ Initialized and ready")
    
    # ────────────────────────────────────────────────
    # EXECUTE AGENT (Engine Level Wrapper)
    # ────────────────────────────────────────────────
    async def execute_agent(self, agent_name: str, task: Any, user_id: Optional[str] = None):
        """
        Engine-level wrapper to execute any agent via runtime.
        This fixes the AttributeError in handle_prompt().
        """
        try:
            logger.info(f"[Engine] Executing agent: {agent_name} (user: {user_id})")

            result = await self.runtime.execute_agent(agent_name, task)

            # Ensure result is always a dict
            if not isinstance(result, dict):
                result = {"response": str(result), "status": "ok"}

            return result

        except Exception as e:
            logger.error(f"[Engine] Failed to execute agent '{agent_name}': {e}", exc_info=True)
            return {
                "error": str(e),
                "status": "error",
                "agent": agent_name
            }

    # ────────────────────────────────────────────────
    # EVENT EMITTER
    # ────────────────────────────────────────────────
    async def emit(self, event_type: str, payload: dict = None):
        """Emit events to the internal bus"""
        try:
            from ..core.message import Message
            message = Message(
                message_type=event_type,
                payload=payload or {},
                sender="engine",
                recipient="all"
            )
            logger.info(f"[EMIT] Publishing {event_type}")
            await self.runtime.bus.publish(message)
        except Exception as e:
            logger.error(f"[ENGINE EMIT ERROR] {e}")

    # ────────────────────────────────────────────────
    # 🔗 CHAIN
    # ────────────────────────────────────────────────
    async def run_agent_chain(self, agents: List[str], task: Dict[str, Any], user_id: str):
        results = {}
        current_input = task.copy()

        self.runtime.add_log(user_id, f"🔗 Chain: {', '.join(agents)}")
        logger.info(f"[Engine] Chain: {agents}")

        for step, agent_name in enumerate(agents):
            key = f"{agent_name}_{step}"

            log_msg = f"  📍 Step {step + 1}: {agent_name}"
            self.runtime.add_log(user_id, log_msg)
            logger.info(f"[Engine] {log_msg}")

            result = await self.execute_agent(agent_name, current_input, user_id=user_id)

            if not isinstance(result, dict):
                result = {"message": str(result)}

            results[key] = result

            if result.get("error"):
                self.runtime.add_log(user_id, f"  ❌ Failed: {result.get('error')}")
                return {
                    "status": "failed",
                    "failed_at": agent_name,
                    "error": result.get("error"),
                    "results": results,
                }

            current_input.update({
                "previous_result": result,
                "chain_step": step,
                "chain_history": results,
                "mode_override": ("fixer" if result.get("mode") == "debugger" else None)
            })

        self.runtime.add_log(user_id, "✅ Chain completed")
        return {
            "status": "success",
            "final_result": current_input,
            "results": results
        }

    def _extract_project_name(self, prompt: str) -> str:
        """Extract clean project name from user prompt"""
        import re
        
        # Remove common build phrases
        clean = re.sub(r'(?i)\b(build|create|make|develop|generate|please|app|website|for me)\b', '', prompt).strip()
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', clean)  # Remove special chars
        
        words = clean.split()[:5]  # Max 5 words
        project_name = "_".join(words).strip("_")
        
        if not project_name or len(project_name) < 3:
            project_name = "nox_app"
            
        return project_name.lower()

    # ────────────────────────────────────────────────
    # 🔥 MAIN ENTRY POINT
    # ────────────────────────────────────────────────
    async def handle_prompt(
            self, prompt: str, user_id: str = "default_user",
            log_callback=None, context: Optional[Dict[str, Any]] = None,
            mode: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Main entry point for chat/build requests - Plan Based"""
        result = None
        decision = {}
        action = "chat"
        start_time = time.time()

        self.runtime.clear_logs(user_id)
        self.runtime.add_log(user_id, f"📝 Request: {prompt[:50]}...")

        # 🔥 STEP 1: PREPROCESS
        pre = await self.execute_agent("preprocessor", {
            "prompt": prompt,
            "user_id": user_id
        }, user_id=user_id)

        # fallback safety
        if not isinstance(pre, dict):
            pre = {"normalized_prompt": prompt}

        normalized_prompt = pre.get("normalized_prompt", prompt)

        self.runtime.add_log(user_id, f"🧠 Normalized: {normalized_prompt[:50]}...")

        if log_callback:
            self.runtime.subscribe_logs(user_id, log_callback)

        try:
            lily = self.runtime.get_agent("lily")
            if not lily:
                raise Exception("Lily agent not found")

            # Get decision from Lily
            decision = await lily.run({
                "prompt": normalized_prompt,
                "user_id": user_id,
                "context": pre,
                "mode": mode
            }) or {}

            action = (decision.get("action") or "chat").lower()

            # Get billing agent
            billing = self.runtime.get_agent("billing_agent")

            # ───── BILLING CHECK FOR PAID ACTIONS ─────
            if action in ["build", "debug", "research", "content_generator"] and billing:
                check = billing.can_perform_action(user_id, action)
                if not check.get("allowed", False):
                    self.runtime.add_log(user_id, f"⛔ Plan limit: {check.get('reason')}")
                    return {
                        "response": f"⛔ {check.get('reason', 'Limit reached').replace('_', ' ').title()}\n\n💎 Upgrade your plan to continue.",
                        "status": "plan_limit",
                        "action": action,
                        "logs": self.runtime.get_logs(user_id),
                    }

            # ───── CONTENT GENERATOR ─────
            if action == "content_generator":
                result = await self.execute_agent("content_generator", {
                    "prompt": normalized_prompt,
                    "user_id": user_id
                }, user_id=user_id)

                if billing:
                    billing.record_usage(user_id, "content_generator")

                return {
                    "response": result.get("message") or "Content generated",
                    "data": result.get("data"),
                    "job_id": result.get("job_id"),
                    "type": "video",
                    "content_type": result.get("type"),
                    "status": "success",
                    "action": "content_generator",
                    "logs": self.runtime.get_logs(user_id),
                }

            # ───── RESEARCH ─────
            if action == "research":
                result = await self.execute_agent("research_agent", {
                    "prompt": normalized_prompt,
                    "user_id": user_id
                }, user_id=user_id)

                if billing:
                    billing.record_usage(user_id, "research")

                return {
                    "response": result.get("summary") or result.get("response") or "Research completed",
                    "logs": self.runtime.get_logs(user_id),
                    "status": "success",
                    "type": "research_result",
                    "action": "research"
                }

            # ───── BUILD ─────
            if action == "build":
                result = await self.execute_agent("app_builder", {
                    "prompt": prompt,
                    "user_id": user_id,
                    "context": context or {},
                    "mode": mode
                }, user_id=user_id)

                if billing:
                    billing.record_usage(user_id, "build")

                # ── Smart Project Name Generation ──
                project_name = result.get("project_name") or self._extract_project_name(prompt)

                # Get ZIP data
                zip_data = self.runtime.get_zip(user_id)

                if zip_data:
                    # Improve filename
                    clean_name = project_name.replace(" ", "_").lower()
                    zip_data["filename"] = f"{clean_name}.zip"
                    zip_data["project_name"] = project_name

                return {
                    "response": result.get("response") or "✅ Build completed successfully!",
                    "zip": zip_data,
                    "project_name": project_name,
                    "logs": self.runtime.get_logs(user_id),
                    "status": "success",
                    "action": "build",
                    "type": "build_result"
                }

                # Extra safety: log if ZIP is missing
                if not zip_data:
                    self.runtime.add_log(user_id, "⚠️ ZIP data not found in runtime")
                    response_data["response"] += "\n\n⚠️ ZIP not available for download."

                return response_data

            # ───── DEBUG ─────
            if action == "debug":
                result = await self.execute_agent("code_assistant", {
                    "prompt": normalized_prompt,
                    "user_id": user_id,
                    "context": pre,
                    "mode": mode
                }, user_id=user_id)

                if billing:
                    billing.record_usage(user_id, "debug")

                return {
                    "type": "code_result",
                    "response": result.get("response", "Debug complete"),
                    "updated_files": result.get("updated_files", {}),
                    "logs": self.runtime.get_logs(user_id),
                    "status": "success",
                    "action": "debug"
                }

            # ───── PLAN LIMIT RESPONSE (from Lily) ─────
            if action == "plan_limit":
                return {
                    "response": decision.get("message", "Plan limit reached"),
                    "status": "plan_limit",
                    "action": "plan_limit",
                    "logs": self.runtime.get_logs(user_id),
                }

            # ───── CHAT (DEFAULT) ─────
            result = await self.execute_agent("chat", {
                "prompt": normalized_prompt,
                "user_id": user_id,
                "context": pre,
                "mode": mode
            }, user_id=user_id)

            return {
                "response": result.get("message", "🤖 Done"),
                "logs": self.runtime.get_logs(user_id),
                "status": "success",
                "action": "chat",
                "type": "message"
            }

        except Exception as e:
            logger.error(f"[ENGINE ERROR] {e}", exc_info=True)

            return {
                "response": f"⚠️ Error: {str(e)}",
                "logs": self.runtime.get_logs(user_id),
                "status": "error",
                "type": "message",
                "action": action
            }

        finally:
            elapsed = time.time() - start_time
            self.runtime.add_log(user_id, f"⏱️ Done in {elapsed:.2f}s")

# ──────────────────────────────────────────────
# GLOBAL SINGLETON
# ──────────────────────────────────────────────
engine = Engine()