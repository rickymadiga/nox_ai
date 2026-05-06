from nox.core.event_bus import EventBus
from plugins.ForgeWatcher.agent import ForgeWatcher as LiveActivityStreamer

def load_agents(registry):

    event_bus = EventBus()
    streamer = LiveActivityStreamer()

    event_bus.subscribe("activity", streamer.handler) 

    # Import agents here
    try:
        from nox.agents.router.agent import RouterAgent
        router = RouterAgent()
        registry.register("task_router", router)
        print("[BOOTSTRAP] RouterAgent loaded")
    except Exception as e:
        print("[BOOTSTRAP] RouterAgent failed:", e)

    try:
        from nox.agents.planner.agent import PlannerAgent
        planner = PlannerAgent()
        registry.register("planner", planner)
        print("[BOOTSTRAP] PlannerAgent loaded")
    except Exception as e:
        print("[BOOTSTRAP] PlannerAgent failed:", e)

    try:
        from nox.agents.app_builder.agent import AppBuilderAgent
        builder = AppBuilderAgent()
        registry.register("app_builder", builder)
        print("[BOOTSTRAP] AppBuilderAgent loaded")
    except Exception as e:
        print("[BOOTSTRAP] AppBuilderAgent failed:", e)   
