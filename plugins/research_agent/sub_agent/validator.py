import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ValidatorAgent:
    """Validate research evidence"""

    def __init__(self, runtime):
        self.runtime = runtime
        self.name = "validator"

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate evidence"""
        
        analysis = task.get("analysis", {})
        sources = task.get("sources", [])
        
        logger.info(f"[{self.name}] Validating evidence from {len(sources)} sources")
        
        quality_score = self._calculate_quality(sources, analysis)
        confidence = self._determine_confidence(quality_score)
        limitations = self._identify_limitations(sources)
        
        return {
            "quality_score": quality_score,
            "confidence": confidence,
            "limitations": limitations,
            "validity": quality_score > 0.6,
            "status": "complete"
        }

    def _calculate_quality(self, sources: list, analysis: dict) -> float:
        """Calculate evidence quality (0-1)"""
        if not sources:
            return 0.0
        
        score = min(len(sources) / 10, 0.8)  # More sources = higher score
        return round(score, 2)

    def _determine_confidence(self, quality_score: float) -> str:
        """Determine confidence level"""
        if quality_score >= 0.8:
            return "high"
        elif quality_score >= 0.5:
            return "medium"
        else:
            return "low"

    def _identify_limitations(self, sources: list) -> list:
        """Identify research limitations"""
        return [
            "Limited to publicly available sources",
            "Search results reflect current web indexing",
            "May not capture very recent developments"
        ]

def register(runtime):
    agent = ValidatorAgent(runtime)
    runtime.register_agent("validator", agent)
    logger.info("[SUB-AGENT] ✅ ValidatorAgent loaded")