# lily.py — NOX GOD BRAIN v18 (Unified Routing + Debug Support + Engine Integration 🧠🔥)

import time
import logging
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class Lily:
    """
    🔥 Lily - The decision-making brain of NOX
    Classifies user intent and routes to appropriate handlers
    """
    
    def __init__(self, runtime=None, user_name: str = "NOX"):
        """
        Initialize Lily brain
        
        Args:
            runtime: Reference to Runtime instance
            user_name: User name (default: NOX)
        """
        self.user_name = user_name
        self.runtime = runtime

        self.system_state: Dict[str, Any] = {
            "active_jobs": {},
            "pending_quotes": {},
            "conversation_history": {},
            "active_context": {},
            "user_credits": {}
        }

        self.step = 0

        # 🔹 INTENT SIGNALS (REFINED - CRITICAL FIX!)
        self.CONFIRM_WORDS = {
            "yes", "yeah", "yep", "sure", "proceed", "confirm", "ok", 
            "go ahead", "do it", "start", "begin", "execute"
        }
        
        self.BUILD_PHRASES = {
            "build", "create", "make", "develop", "generate", "i want",
            "i need", "can you", "could you", "would you", "please make",
            "please build", "please create", "construct", "write app",
            "write application", "build app", "create app", "make app",
            "build website", "create website"
        }
        
        self.REFINE_WORDS = {
            "change", "modify", "add", "remove", "update", "improve",
            "refine", "adjust", "tweak", "edit", "alter", "different",
            "different one", "try again", "another"
        }
        
        # 🔹 DEBUG WORDS (FIXED - MOVED BEFORE BUILD!)
        self.DEBUG_WORDS = {
            "fix", "bug", "error", "debug", "traceback", "issue", "problem",
            "crash", "exception", "failure", "not working", "help with code",
            "code issue", "review code", "check this", "what's wrong",
            "broken", "doesn't work", "fix this code", "debug this",
            "find bug", "refactor", "optimize", "improve code"
        }
        
        # 🔹 RESEARCH WORDS
        self.RESEARCH_WORDS = {
            "research", "search", "find", "lookup", "look up", "what is",
            "who is", "tell me about", "explain", "summarize", "latest",
            "news about", "information on", "sources", "papers", "study",
            "how does", "why is", "web search", "google", "wikipedia",
            "facts about", "data on", "statistics on", "current events",
            "trends in", "academic research"
        }
        
        logger.info("[LILY] Initialized - Ready to make decisions 🧠")

    # ────────────────────────────────────────────────
    # RUNTIME INTEGRATION
    # ────────────────────────────────────────────────
    
    def attach_runtime(self, runtime) -> None:
        """
        🔥 Attach runtime and subscribe to events
        
        Args:
            runtime: Runtime instance
        """
        self.runtime = runtime
        
        # Subscribe to key events
        if hasattr(runtime, 'bus'):
            self.runtime.bus.subscribe("forge_complete", self.on_forge_complete)
            self.runtime.bus.subscribe("build_complete", self.on_build_complete)
        
        logger.info("[LILY] v18 — Unified Orchestrator ACTIVE 🔥")

    async def on_forge_complete(self, message: Any) -> None:
        """Handle forge completion event"""
        try:
            payload = (
                message.payload
                if hasattr(message, "payload")
                else message.get("payload", {})
            )
            user_id = payload.get("user_id", "default_user")
            
            logger.info(f"[LILY] 🎉 Build completed for {user_id}")
            
            # Store in system state for reference
            if user_id in self.system_state["active_jobs"]:
                self.system_state["active_jobs"][user_id]["completed_at"] = time.time()
                
        except Exception as e:
            logger.error(f"[LILY] Error in on_forge_complete: {e}", exc_info=True)

    async def on_build_complete(self, message: Any) -> None:
        """Handle build completion event"""
        try:
            payload = (
                message.payload
                if hasattr(message, "payload")
                else message.get("payload", {})
            )
            user_id = payload.get("user_id", "default_user")
            status = payload.get("status", "unknown")
            
            logger.info(f"[LILY] Build status for {user_id}: {status}")
            
        except Exception as e:
            logger.error(f"[LILY] Error in on_build_complete: {e}", exc_info=True)

    # ────────────────────────────────────────────────
    # CONVERSATION HISTORY
    # ────────────────────────────────────────────────
    
    def _get_history(self, user_id: str) -> deque:
        """Get conversation history for user"""
        if user_id not in self.system_state["conversation_history"]:
            self.system_state["conversation_history"][user_id] = deque(maxlen=20)
        return self.system_state["conversation_history"][user_id]

    def _add_to_history(self, user_id: str, role: str, content: str) -> None:
        """Add message to conversation history"""
        try:
            self._get_history(user_id).append({
                "role": role,
                "content": content,
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"[LILY] Error adding to history: {e}")

    def get_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user
        
        Args:
            user_id: User identifier
            limit: Max messages to return
        
        Returns:
            List of conversation messages
        """
        history = self._get_history(user_id)
        return list(history)[-limit:]

    # ────────────────────────────────────────────────
    # INTENT CLASSIFICATION (CRITICAL FIX!)
    # ────────────────────────────────────────────────
    def classify_intent(self, text: str, user_id: Optional[str] = None) -> str:
        """
        Enhanced intent classification with CORRECT priority order.
        CRITICAL: DEBUG must be checked BEFORE BUILD!
        """
        t = text.lower().strip()
        logger.debug(f"[LILY] Classifying: {t[:80]}...")

        # ✅ PRIORITY 1: RESEARCH (High specificity)
        if any(w in t for w in self.RESEARCH_WORDS):
            logger.info("[LILY] Intent → research")
            return "research"

        # ✅ PRIORITY 2: DEBUG/FIX (CHECK BEFORE BUILD!)
        if any(w in t for w in self.DEBUG_WORDS):
            logger.info("[LILY] Intent → debug")
            return "debug"

        # ✅ PRIORITY 3: BUILD (Generic build phrases)
        if any(p in t for p in self.BUILD_PHRASES):
            logger.info("[LILY] Intent → build")
            return "build"

        # ✅ PRIORITY 4: CONTENT GENERATION
        content_keywords = {
            "generate image", "create image", "make image", "image of",
            "picture of", "generate photo", "draw", "illustrate",
            "generate video", "create video", "make video", "video about",
            "clip of", "write a story", "write an article", "write a poem",
            "write about", "generate text", "create content", "blog post",
            "essay", "script", "review this", "quality check",
            "evaluate content", "improve this text", "rate this writing"
        }

        if any(kw in t for kw in content_keywords):
            logger.info("[LILY] Intent → content_generation")
            return "content_generation"

        # ✅ PRIORITY 5: QUOTE/CONFIRMATION (For pending quotes)
        if user_id and user_id in self.system_state["pending_quotes"]:
            if any(w in t for w in self.CONFIRM_WORDS):
                logger.info("[LILY] Intent → confirm")
                return "confirm"
            if any(w in t for w in self.REFINE_WORDS):
                logger.info("[LILY] Intent → refine")
                return "refine"

        # ✅ PRIORITY 6: DEFAULT TO CHAT
        logger.info("[LILY] Intent → chat (fallback)")
        return "chat"


    # ────────────────────────────────────────────────
    # AGENT EXECUTION
    # ────────────────────────────────────────────────
    
    async def call_agent(self, agent_name: str, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Call an agent to execute a task
        
        Args:
            agent_name: Name of agent to call
            task: Task to execute
        
        Returns:
            Agent result or None
        """
        if not self.runtime:
            logger.warning(f"[LILY] No runtime attached - cannot call {agent_name}")
            return None
        
        try:
            logger.info(f"[LILY] Calling agent: {agent_name}")
            result = await self.runtime.execute_agent(agent_name, task)
            logger.info(f"[LILY] Agent {agent_name} completed")
            return result
        except Exception as e:
            logger.error(f"[LILY] Error calling agent {agent_name}: {e}", exc_info=True)
            return None

    # ────────────────────────────────────────────────
    # 🚀 MAIN ORCHESTRATION
    # ────────────────────────────────────────────────
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔥 Main decision-making logic - Plan Based
        """
        user_input = task.get("prompt", "")
        user_id = task.get("user_id", "default_user")
        context = task.get("context", {}).copy()

        logger.info(f"[LILY] pending_quotes={list(self.system_state['pending_quotes'].keys())}")

        # 🔹 Classify intent
        intent = self.classify_intent(user_input, user_id)
        self._add_to_history(user_id, "user", user_input)

        logger.info(f"[LILY] Processing {intent} for {user_id}")

        # Get billing agent
        billing = None
        if self.runtime:
            billing = self.runtime.get_agent("billing_agent")

        # ───── RESEARCH ROUTE ─────
        if intent == "research":
            if billing:
                check = billing.can_perform_action(user_id, "research")
                if not check["allowed"]:
                    return {
                        "action": "plan_limit",
                        "message": f"❌ Research limit reached. Upgrade to Pro!",
                        "suggest_upgrade": True
                    }

            return {
                "action": "research",
                "prompt": user_input,
                "context": context,
                "message": "🔬 Starting research..."
            }

        # ───── DEBUG ROUTE ─────
        if intent == "debug":
            if billing:
                check = billing.can_perform_action(user_id, "debug")
                if not check["allowed"]:
                    return {
                        "action": "plan_limit",
                        "message": f"❌ Debug limit reached. Upgrade to Pro for more fixes!",
                        "suggest_upgrade": True
                    }

            return {
                "action": "debug",
                "prompt": user_input,
                "context": context,
                "message": "🛠️ Analyzing and fixing your code..."
            }

        # ───── CONTENT GENERATION ─────
        if intent == "content_generation":
            if billing:
                check = billing.can_perform_action(user_id, "content_generator")
                if not check["allowed"]:
                    return {
                        "action": "plan_limit",
                        "message": f"❌ Content generation limit reached.",
                        "suggest_upgrade": True
                    }

            return {
                "action": "content_generator",
                "prompt": user_input,
                "context": context,
                "message": "🎨 Generating content..."
            }

        # ───── BUILD ROUTE (Direct - No Quote) ─────
        if intent == "build":
            logger.info(f"[LILY] 🏗️ Build request for {user_id}")
            
            if billing:
                # TODO: Improve complexity detection later
                complexity = "complex" if any(word in user_input.lower() for word in 
                    ["full", "complete", "advanced", "dashboard", "ecommerce", "ai", "real-time"]) else "medium"
                
                can_build = billing.can_perform_action(user_id, "build", complexity=complexity)

                if not can_build["allowed"]:
                    return {
                        "action": "plan_limit",
                        "message": f"❌ {can_build['reason'].replace('_', ' ').title()}\n\n💎 Upgrade to **Pro** for more builds and complex projects!",
                        "suggest_upgrade": True
                    }

            logger.info(f"[LILY] ✅ Build allowed for {user_id}")
            return {
                "action": "build",
                "prompt": user_input,
                "context": context,
                "message": "🏗️ Starting build..."
            }

        # ───── CHAT (DEFAULT) ─────
        logger.info(f"[LILY] 💬 Chat mode for {user_id}")
        return {
            "action": "chat",
            "prompt": user_input,
            "context": context,
            "message": "💬 Processing your request..."
        }

    # ────────────────────────────────────────────────
    # HELPER METHODS
    # ────────────────────────────────────────────────
    
    def get_pending_quote(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get pending quote for user"""
        return self.system_state["pending_quotes"].get(user_id)

    def clear_pending_quote(self, user_id: str) -> None:
        """Clear pending quote for user"""
        if user_id in self.system_state["pending_quotes"]:
            del self.system_state["pending_quotes"][user_id]

    def get_active_job(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get active job for user"""
        return self.system_state["active_jobs"].get(user_id)

    def set_active_job(self, user_id: str, job_data: Dict[str, Any]) -> None:
        """Set active job for user"""
        self.system_state["active_jobs"][user_id] = {
            **job_data,
            "started_at": time.time()
        }

    def clear_active_job(self, user_id: str) -> None:
        """Clear active job for user"""
        if user_id in self.system_state["active_jobs"]:
            del self.system_state["active_jobs"][user_id]

    def get_status(self) -> Dict[str, Any]:
        """Get Lily's current status"""
        return {
            "name": "Lily",
            "version": "v18",
            "active_jobs": len(self.system_state["active_jobs"]),
            "pending_quotes": len(self.system_state["pending_quotes"]),
            "has_runtime": self.runtime is not None
        }


# ────────────────────────────────────────────────
# REGISTRATION
# ────────────────────────────────────────────────

def register(runtime) -> None:
    """
    Register Lily with the runtime
    
    Args:
        runtime: Runtime instance
    """
    try:
        lily = Lily(runtime=runtime)
        runtime.register_agent("lily", lily)
        logger.info("[LILY] ✅ Registered with runtime")
    except Exception as e:
        logger.error(f"[LILY] Registration failed: {e}", exc_info=True)
