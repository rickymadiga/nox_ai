import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate formatted research report"""

    def __init__(self, runtime):
        self.runtime = runtime
        self.name = "report_generator"

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate research report"""
        
        query = task.get("query", "")
        sources = task.get("sources", [])
        analysis = task.get("analysis", {})
        validation = task.get("validation", {})
        synthesis = task.get("synthesis", {})
        
        logger.info(f"[{self.name}] Generating report")
        
        report = {
            "title": f"Research Report: {query}",
            "timestamp": datetime.utcnow().isoformat(),
            "executive_summary": synthesis.get("summary", ""),
            "key_findings": analysis.get("findings", []),
            "conclusions": synthesis.get("conclusions", []),
            "recommendations": synthesis.get("recommendations", []),
            "evidence_quality": validation.get("quality_score", 0),
            "confidence_level": validation.get("confidence", "medium"),
            "limitations": validation.get("limitations", []),
            "sources_cited": len(sources),
            "citations": self._format_citations(sources)
        }
        
        return report

    def _format_citations(self, sources: List[Dict]) -> List[str]:
        """Format citations"""
        citations = []
        for i, source in enumerate(sources, 1):
            citation = f"[{i}] {source.get('title', 'Unknown')} - {source.get('url', 'N/A')}"
            citations.append(citation)
        return citations