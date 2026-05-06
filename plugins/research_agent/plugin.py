import logging
from plugins.research_agent.sub_agent.research_agent import ResearchAgent
from plugins.research_agent.sub_agent.decomposer import DecomposerAgent
from plugins.research_agent.sub_agent.web_searcher import WebSearcherAgent
from plugins.research_agent.sub_agent.analyzer import AnalyzerAgent
from plugins.research_agent.sub_agent.validator import ValidatorAgent
from plugins.research_agent.sub_agent.synthesizer import SynthesizerAgent
from plugins.research_agent.sub_agent.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

def register(runtime):
    """Register all research agents with runtime"""
    
    try:
        logger.info("[RESEARCH] 🔬 Starting registration...")
        
        # Sub-agents
        agents = [
            ("decomposer", DecomposerAgent(runtime)),
            ("searcher", WebSearcherAgent(runtime)),
            ("analyzer", AnalyzerAgent(runtime)),
            ("validator", ValidatorAgent(runtime)),
            ("synthesizer", SynthesizerAgent(runtime)),
            ("report_generator", ReportGenerator(runtime)),
        ]
        
        for name, agent in agents:
            runtime.register_agent(name, agent)
            logger.info(f"[RESEARCH] ✅ {name} registered")
        
        # Main research agent
        research_agent = ResearchAgent(runtime)
        runtime.register_agent("research_agent", research_agent)
        logger.info("[RESEARCH] ✅ research_agent registered")
        
        # Capability
        runtime.register_capability(
            agent_name="research_agent",
            intent="research",
            keywords=[
                "research", "search", "find", "gather information",
                "analyze", "summarize", "web search", "lookup",
                "what is", "tell me about", "explain", "latest",
                "news about", "how does", "current"
            ]
        )
        
        logger.info("[RESEARCH] 🔬 All agents registered!")
        
    except Exception as e:
        logger.error(f"[RESEARCH] ❌ Failed: {e}", exc_info=True)
        raise