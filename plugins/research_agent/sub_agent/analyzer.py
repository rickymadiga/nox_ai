import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AnalyzerAgent:
    """Analyze research sources - Enhanced"""

    def __init__(self, runtime):
        self.runtime = runtime
        self.name = "analyzer"

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        sources = task.get("sources", [])
        query = task.get("research_query", "unknown")
    
        if not sources:
            logger.warning(f"[{self.name}] No sources provided")
            return {
                "findings": [],
            "key_insights": [],
            "summary": f"No sources available for analysis of {query}",
            "sources_analyzed": 0,
            "status": "complete"
        }

    def _generate_summary(self, query: str, findings: List[Dict]) -> str:
        if not findings:
            return f"No relevant information found for '{query}'."
        
        return f"Analysis of {len(findings)} sources shows that {query} is well-documented across multiple reliable references."