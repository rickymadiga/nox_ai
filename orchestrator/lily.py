# lily.py — NOX GOD BRAIN v18 (Unified Routing + Debug Support + Engine Integration 🧠🔥)

import time
import re
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
            "build", "create", "make", "develop", "generate", "write app", "build app",
            "create app", "make app", "build website", "create website", "develop app"
        }
        
        self.REFINE_WORDS = {
            "change", "modify", "add", "remove", "update", "improve",
            "refine", "adjust", "tweak", "edit", "alter", "different",
            "different one", "try again", "another"
        }
        
        # 🔹 DEBUG WORDS (FIXED - MOVED BEFORE BUILD!)
        self.DEBUG_WORDS = {
            "fix", "bug", "error", "debug", "traceback", "issue", "problem", "crash",
            "exception", "not working", "doesn't work", "broken", "help with code",
            "fix this", "debug this", "review code", "what's wrong"
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
    # INTENT CLASSIFICATION (Improved)
    # ────────────────────────────────────────────────

    def classify_intent(self, text: str, user_id: Optional[str] = None) -> str:
        """
        Improved intent classification with video + research awareness.
        """
        if not text or not text.strip():
            return "chat"

        t = text.lower().strip()
        original_text = text.strip()

        def contains_any(text: str, words: set) -> bool:
            return any(word in text for word in words)

        # ───── PRIORITY 1: DEBUG ─────
        if contains_any(t, self.DEBUG_WORDS):
            if not contains_any(t, self.BUILD_PHRASES) or any(phrase in t for phrase in ["fix bug", "debug code", "fix error"]):
                logger.info("[LILY] Intent → debug")
                return "debug"

        # ───── PRIORITY 2: RESEARCH / QUESTIONS ─────
        is_question = "?" in original_text or any(q in t for q in ["what", "who", "when", "where", "why", "how", "explain", "tell me"])
        
        if (contains_any(t, self.RESEARCH_WORDS) or 
            is_question and len(t.split()) >= 3):
            logger.info("[LILY] Intent → research")
            return "research"

        # ───── PRIORITY 3: VIDEO WITH RESEARCH ─────
        video_keywords = {"video", "make video", "generate video", "create video", "youtube video"}
        if contains_any(t, video_keywords):
            # If video is about a specific topic/fact → use research first
            if any(word in t for word in ["about", "on", "explaining", "story of", "history of", "facts about", "documentary"]):
                logger.info("[LILY] Intent → video_with_research")
                return "video_with_research"
            else:
                logger.info("[LILY] Intent → content_generation (video)")
                return "content_generation"

        # ───── PRIORITY 4: MATH ─────
        math_pattern = re.compile(r'\b(\d+[\s+\-*/^]+\d+|\d+\s*(plus|minus|times|divided by|multiplied by)\s*\d+)\b')
        if (contains_any(t, {"calculate", "compute", "sum", "total", "how much"}) or 
            math_pattern.search(t) or 
            any(c in t for c in "+-*/") and any(char.isdigit() for char in t)):
            logger.info("[LILY] Intent → math")
            return "math"

        # ───── PRIORITY 5: BUILD ─────
        if contains_any(t, self.BUILD_PHRASES):
            logger.info("[LILY] Intent → build")
            return "build"

        # ───── PRIORITY 6: GENERAL CONTENT GENERATION ─────
        content_keywords = {"generate image", "create image", "make image", "draw", "story", "poem", "song lyrics"}
        if contains_any(t, content_keywords) or any(kw in t for kw in ["image of", "picture of", "photo of"]):
            logger.info("[LILY] Intent → content_generation")
            return "content_generation"

        # ───── PRIORITY 7: REFINE / CONFIRM ─────
        if user_id and user_id in self.system_state.get("pending_quotes", {}):
            if contains_any(t, self.CONFIRM_WORDS):
                return "confirm"
            if contains_any(t, self.REFINE_WORDS):
                return "refine"

        # ───── DEFAULT ─────
        logger.info(f"[LILY] Intent → chat (fallback) | Text: {t[:80]}...")
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
    🔥  Main orchestration logic - Improved version
        """
        user_input = task.get("prompt", "").strip()
        user_id = task.get("user_id", "default_user")
        context = task.get("context", {}).copy()

        if not user_input:
            return {
                "action": "chat",
                "message": "I didn't receive any input. How can I help you?",
                "prompt": ""
            }

        # Add to history
        self._add_to_history(user_id, "user", user_input)

        # Classify intent
        intent = self.classify_intent(user_input, user_id)

        logger.info(f"[LILY] User: {user_id} | Intent: {intent} | Input: {user_input[:120]}...")

        # Get billing agent once
        billing = self.runtime.get_agent("billing_agent") if self.runtime else None

        # ───── INTENT ROUTING ─────

        if intent == "research":
            if billing and not billing.can_perform_action(user_id, "research")["allowed"]:
                return self._plan_limit_response("research")
        
            return {
                "action": "research",
                "prompt": user_input,
                "context": context,
                "message": "🔬 Researching your query..."
            }

        elif intent == "debug":
            if billing and not billing.can_perform_action(user_id, "debug")["allowed"]:
                return self._plan_limit_response("debug")
        
            return {
                "action": "debug",
                "prompt": user_input,
                "context": context,
                "message": "🛠️ Analyzing and debugging your code..."
            }

        elif intent == "math":
            if billing and not billing.can_perform_action(user_id, "math")["allowed"]:
                return self._plan_limit_response("math")
        
            return {
                "action": "math",
                "prompt": user_input,
                "context": context,
                "message": "📐 Computing your calculation..."
            }

        elif intent == "build":
            # Determine complexity
            complexity = self._detect_complexity(user_input)
        
            if billing:
                check = billing.can_perform_action(user_id, "build", complexity=complexity)
                if not check["allowed"]:
                    return self._plan_limit_response("build", complexity)

            return {
                "action": "build",
                "prompt": user_input,
                "context": context,
                "message": f"🏗️ Starting {complexity} build...",
                "complexity": complexity
            }

        elif intent == "content_generation":
            if billing and not billing.can_perform_action(user_id, "content_generator")["allowed"]:
                return self._plan_limit_response("content_generation")
        
            return {
                "action": "video_with_research" if intent == "video_with_research" else "content_generation",
                "prompt": user_input,
                "context": context,
                "message": "🔬 Researching + 🎬 Generating informed video...",
                "needs_research": True
            }

        elif intent == "confirm" and user_id in self.system_state.get("pending_quotes", {}):
            return {
                "action": "confirm",
                "prompt": user_input,
                "context": context,
                "message": "✅ Confirmed. Proceeding with previous request..."
            }

        elif intent == "refine" and user_id in self.system_state.get("pending_quotes", {}):
            return {
                "action": "refine",
                "prompt": user_input,
                "context": context,
                "message": "🔄 Refining your previous request..."
           }

        # ───── DEFAULT: CHAT / GENERAL ─────
        else:
            logger.info(f"[LILY] Falling back to general chat for: {user_input[:80]}...")
            
            # Smart fallback: route question-like inputs to research
            return {
                "action": "research" if self._is_research_like(user_input) else "chat",
                "prompt": user_input,
                "context": context,
                "message": "💬 Got it. How can I assist you today?"
            }

    # ────────────────────────────────────────────────
    # HELPER METHODS
    # ────────────────────────────────────────────────

    def _plan_limit_response(self, action: str, complexity: str = None) -> Dict[str, Any]:
        """Standardized plan limit response"""
        messages = {
            "research": "❌ Research limit reached.",
            "debug": "❌ Debug limit reached.",
            "math": "❌ Calculation limit reached.",
            "build": f"❌ Build limit reached for {complexity or 'this'} project.",
            "content_generation": "❌ Content generation limit reached."
        }
    
        return {
            "action": "plan_limit",
            "message": messages.get(action, "❌ Action limit reached.") + 
                       "\n\n💎 Upgrade to **Pro** for unlimited access!",
            "suggest_upgrade": True
        }


    def _detect_complexity(self, text: str) -> str:
        """Detect project complexity for build requests"""
        text_lower = text.lower()
        high_complexity_indicators = {
            "full", "complete", "advanced", "dashboard", "ecommerce", "ai", 
            "real-time", "multi-user", "authentication", "database", "backend", 
            "full stack", "admin panel", "management system"
        }
    
        if any(indicator in text_lower for indicator in high_complexity_indicators):
            return "complex"
        elif any(word in text_lower for word in ["simple", "basic", "small", "quick"]):
            return "simple"
        else:
            return "medium"
        
    def _is_research_like(self, text: str) -> bool:
        """
        Determine if a chat message should be routed to research
        """
        if not text:
            return False
        
        t = text.lower().strip()
        
        # Simple heuristics for general questions
        research_indicators = [
            "what", "who", "when", "where", "why", "how", 
            "explain", "tell me about", "difference between",
            "latest", "current", "news", "update on"
        ]
        
        return any(indicator in t for indicator in research_indicators) or "?" in text    
    
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
   
    def _add_to_history(self, user_id: str, role: str, content: str) -> None:
        if user_id not in self.system_state["conversation_history"]:
            self.system_state["conversation_history"][user_id] = deque(maxlen=20)
        self.system_state["conversation_history"][user_id].append({
            "role": role, "content": content, "timestamp": time.time()
        })

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": "Lily",
            "version": "v19",
            "active_jobs": len(self.system_state["active_jobs"]),
            "pending_quotes": len(self.system_state.get("pending_quotes", {})),
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
