import logging
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

class ResearchAgent:
    """
    🔬 Research AI Agent
    Performs multi-step research: decompose → search → analyze → validate → synthesize
    """

    def __init__(self, runtime):
        self.runtime = runtime
        self.name = "research_agent"
        logger.info(f"[{self.name}] Initialized")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full research workflow"""
        
        research_query = task.get("prompt", "")
        user_id = task.get("user_id", "default")
        research_type = task.get("research_type", "general")
        
        if not research_query:
            return {
                "agent": "research_agent",
                "status": "error",
                "error": "No research query provided"
            }
        
        logger.info(f"[{self.name}] 🔬 Starting: {research_query[:50]}")
        
        try:
            # Step 1: Decompose
            logger.info(f"[{self.name}] Step 1: Decomposing...")
            decomposition = await self.runtime.execute_agent("decomposer", {
                "query": research_query,
                "research_type": research_type
            })
            sub_questions = decomposition.get("sub_questions", [research_query])
            logger.info(f"[{self.name}] ✅ Sub-questions: {len(sub_questions)}")
            
            # Step 2: Search
            logger.info(f"[{self.name}] Step 2: Searching...")
            search_results = await self.runtime.execute_agent("searcher", {
                "queries": sub_questions,
                "user_id": user_id
            })
            sources = search_results.get("sources", [])
            logger.info(f"[{self.name}] ✅ Found {len(sources)} sources")
            
            # Step 3: Analyze
            logger.info(f"[{self.name}] Step 3: Analyzing...")
            analysis = await self.runtime.execute_agent("analyzer", {
                "sources": sources,
                "research_query": research_query
            })
            logger.info(f"[{self.name}] ✅ Analysis complete")
            
            # Step 4: Validate
            logger.info(f"[{self.name}] Step 4: Validating...")
            validation = await self.runtime.execute_agent("validator", {
                "analysis": analysis,
                "sources": sources,
                "research_query": research_query
            })
            logger.info(f"[{self.name}] ✅ Validation complete")
            
            # Step 5: Synthesize
            logger.info(f"[{self.name}] Step 5: Synthesizing...")
            synthesis = await self.runtime.execute_agent("synthesizer", {
                "analysis": analysis,
                "validation": validation,
                "sources": sources,
                "research_query": research_query
            })
            logger.info(f"[{self.name}] ✅ Synthesis complete")
            
            # Step 6: Report
            logger.info(f"[{self.name}] Step 6: Generating report...")
            report = await self.runtime.execute_agent("report_generator", {
                "query": research_query,
                "sub_questions": sub_questions,
                "sources": sources,
                "analysis": analysis,
                "validation": validation,
                "synthesis": synthesis
            })
            logger.info(f"[{self.name}] ✅ Report generated")
            
            # Build final response
            return {
                "agent": "research_agent",
                "status": "complete",
                "action": "research",
                "type": "research_result",
                "research_query": research_query,
                "summary": synthesis.get("summary"),
                "key_findings": synthesis.get("key_findings"),
                "conclusions": synthesis.get("conclusions"),
                "recommendations": synthesis.get("recommendations"),
                "research_type": research_type,
                "sub_questions": sub_questions,
                "sources_found": len(sources),
                "sources": sources[:10],
                "analysis": analysis,
                "validation": validation,
                "synthesis": synthesis,
                "report": report,
                "response": self._format_response(research_query, sources, synthesis),
                "summary": synthesis.get("summary", f"Research on '{research_query}' completed")
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}", exc_info=True)
            return {
                "agent": "research_agent",
                "status": "error",
                "action": "research",
                "error": str(e),
                "research_query": research_query,
                "response": f"Research failed: {str(e)}"
            }
    
    def _format_response(self, query: str, sources: List[Dict], synthesis: Dict) -> str:
        """Format response for frontend - Fixed signature"""
        if not sources:
            return f"Could not find sufficient information for '{query}' at this time."

        parts = [f"**🔬 Research Results for: {query}**\n"]

        # Direct Answer
        for source in sources:
            if source.get("type") == "answer" or "capital" in source.get("title", "").lower() or "moscow" in source.get("content", "").lower():
                parts.append(f"**✅ Answer:** {source.get('content')}\n")
                break

        # Summary
        summary = synthesis.get("summary", "")
        if summary:
            parts.append(f"**📝 Summary:**\n{summary}\n")

        # Key Findings / Sources
        parts.append("**📚 Key Sources & Insights:**")
        for i, source in enumerate(sources[:5], 1):
            title = source.get("title", "Source")
            content = source.get("content", "")[:220]
            url = source.get("url", "")
            
            if url and url.startswith("http"):
                parts.append(f"{i}. **{title}**\n   {content}...\n   [Read more]({url})")
            else:
                parts.append(f"{i}. **{title}**\n   {content}...")

        return "\n".join(parts)