import logging
from .agent import ContentGeneratorAgent

logger = logging.getLogger(__name__)

def register(runtime):
    """
    Register the ContentGeneratorAgent.
    The runtime already provides video_manager.
    """
    video_manager = getattr(runtime, 'video_manager', None)

    agent_instance = ContentGeneratorAgent(runtime, video_manager)

    runtime.register_agent(
        "content_generator", 
        agent_instance
    )

    runtime.register_capability(
        agent_name="content_generator",
        intent="content_generation",
        keywords=[
            "story", "write", "article", "essay", "blog", "poem", "describe", 
            "explain", "summarize", "generate text",
            "generate image", "create image", "image from text",
            "generate video", "create video", "video clip",
            "review", "quality check", "evaluate content", "improve text"
        ]
    )

    logger.info("[PLUGIN] ContentGeneratorAgent registered successfully with video_manager")