import asyncio
import sys
import logging
from typing import Final, List, Tuple, Dict, Any

from ..core.event_bus import EventBus
from ..core.message import Message
from ..memory.memory import Memory

from ..agents.planner import PlannerAgent
from ..agents.coder import Coder
from ..agents.tester import Tester
from ..agents.reviewer import Reviewer
from ..agents.debugger import Debugger
from ..agents.assembler import Assembler
from ..agents.fixer import Fixer
from ..agents.executor import Executor

logger = logging.getLogger(__name__)

# 🔥 AGENT REGISTRY - Order matters for pipeline flow
AGENTS: List[Tuple[type, str]] = [
    (PlannerAgent, "planner"),
    (Coder, "coder"),
    (Executor, "executor"),
    (Tester, "tester"),
    (Reviewer, "reviewer"),
    (Debugger, "debugger"),
    (Fixer, "fixer"),
    (Assembler, "assembler"),
]

INITIAL_WAIT_AFTER_TASK: Final[float] = 15.0  # 🔥 Increased for full pipeline


async def create_and_register_agents(bus: EventBus, context: dict) -> Dict[str, Any]:
    """
    🔥 Create and register all agents in pipeline
    
    Args:
        bus: Event bus instance
        context: Runtime context
    
    Returns:
        Dictionary of created agents
    """
    logger.info("[ARENA] Creating and registering agents...")
    print("[Arena] Creating and registering agents...\n")

    context["agents"] = []
    agents_dict = {}

    # ✅ Helper to access agents globally
    def get_agent(name):
        for a in context["agents"]:
            if a.name == name:
                return a
        return None

    context["get_agent"] = get_agent

    for agent_class, agent_name in AGENTS:
        try:
            # 🔥 CRITICAL: Pass name, bus, and context
            agent = agent_class(agent_name, bus, context)

            # Inject runtime if available
            if hasattr(agent, "runtime"):
                agent.runtime = context.get("runtime")

            # Register event subscriptions
            agent.register()

            context["agents"].append(agent)
            agents_dict[agent_name] = agent

            logger.info(f"[ARENA] {agent_name.capitalize()} registered ✅")
            print(f"[Arena] {agent_name.capitalize()} registered")

        except TypeError as e:
            logger.error(f"[ARENA] Agent init error for {agent_name}: {e}")
            print(f"[Arena] ❌ Error initializing {agent_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"[ARENA] Unexpected error with {agent_name}: {e}")
            print(f"[Arena] ❌ Unexpected error: {e}")
            raise

    print("\n[Arena] All agents registered successfully.\n")
    logger.info("[ARENA] All agents registered successfully")
    return agents_dict


async def run_task_pipeline(bus: EventBus, task: str) -> None:
    """Run a task through the pipeline"""

    # 🔥 Create proper Message object
    message = Message(
        sender="arena",
        recipient="planner",
        message_type="TASK_REQUEST",
        payload={"task": task.strip()},
    )

    logger.info(f"[ARENA] Publishing task: {task}")
    print(f"[Arena] → Publishing task: {task!r}")

    await bus.publish(message)

    logger.info(f"[ARENA] Waiting {INITIAL_WAIT_AFTER_TASK:.1f}s for pipeline completion")
    print(f"[Arena] Waiting {INITIAL_WAIT_AFTER_TASK:.1f}s...\n")

    await asyncio.sleep(INITIAL_WAIT_AFTER_TASK)

    print("[Arena] Pipeline cycle finished.\n")
    logger.info("[ARENA] Pipeline cycle finished")


async def run_forge(task: str, runtime=None, user_id: str = "default_user") -> Dict[str, Any]:
    """
    🔥 Main forge execution function
    
    Args:
        task: Build task/prompt
        runtime: Optional runtime instance
        user_id: User identifier
    
    Returns:
        Build result
    """

    # 🔥 Reuse runtime bus if available
    if runtime and hasattr(runtime, "bus"):
        bus = runtime.bus
        logger.info("[FORGE] Using runtime bus")
    else:
        bus = EventBus()
        logger.info("[FORGE] Created new EventBus")

    # 🔥 Shared context
    context = {
        "bus": bus,
        "runtime": runtime,
        "user_id": user_id
    }

    # Memory
    try:
        memory = Memory("memory", bus, context)
        context["memory"] = memory
        logger.info("[FORGE] Memory initialized")
    except Exception as e:
        logger.warning(f"[FORGE] Memory initialization failed: {e}")
        context["memory"] = None

    # 🔥 CREATE AND REGISTER ALL AGENTS
    try:
        agents_dict = await create_and_register_agents(bus, context)
    except Exception as e:
        logger.error(f"[FORGE] Agent registration failed: {e}")
        return {
            "status": "error",
            "error": f"Agent registration failed: {str(e)}",
            "task": task,
            "user_id": user_id
        }

    # 🔥 RESULT HOLDER
    result_container = {"result": None}

    # 🔥 LISTENER FOR COMPLETION
    async def on_complete(message):
        """Handle forge completion"""
        logger.info("[FORGE] forge_complete event received")
        print("[Arena] ✅ forge_complete received")

        # Handle both Message object and dict
        if hasattr(message, "payload"):
            result_container["result"] = message.payload
        else:
            result_container["result"] = message.get("payload", {})

    bus.subscribe("forge_complete", on_complete)

    # 🔥 START PIPELINE - Use Message object
    logger.info(f"[FORGE] Starting pipeline for task: {task}")
    print(f"[Arena] Starting pipeline...\n")

    # 🔥 CRITICAL: Create proper Message object
    start_message = Message(
        sender="arena",
        recipient="planner",
        message_type="TASK_REQUEST",
        payload={
            "task": str(task).strip() if task else "",
            "user_id": user_id,
            "prompt": str(task).strip() if task else ""
        }
    )

    await bus.publish(start_message)

    logger.info(f"[FORGE] Waiting for completion (max {INITIAL_WAIT_AFTER_TASK}s)...")
    print(f"[Arena] Waiting for completion...\n")

    # 🔥 WAIT UNTIL RESULT OR TIMEOUT
    max_iterations = int(INITIAL_WAIT_AFTER_TASK)
    for i in range(max_iterations):
        if result_container["result"] is not None:
            logger.info(f"[FORGE] Result received after {i}s, breaking wait loop")
            print(f"[Arena] Result received!\n")
            break
        
        await asyncio.sleep(1)
        
        # Log progress every 3 seconds
        if (i + 1) % 3 == 0:
            logger.debug(f"[FORGE] Still waiting... ({i+1}s elapsed)")

    print("[Arena] Pipeline cycle finished.\n")
    logger.info("[FORGE] Pipeline cycle finished")

    # 🔥 RETURN REAL RESULT
    if result_container["result"] is not None:
        logger.info(f"[FORGE] Build completed successfully")
        return result_container["result"]
    else:
        logger.warning(f"[FORGE] Build timed out after {INITIAL_WAIT_AFTER_TASK}s")
        return {
            "status": "timeout",
            "task": task,
            "user_id": user_id,
            "message": f"Build process timed out after {INITIAL_WAIT_AFTER_TASK}s"
        }