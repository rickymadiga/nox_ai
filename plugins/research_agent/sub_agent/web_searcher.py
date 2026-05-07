import aiohttp
import os
import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class WebSearcherAgent:
    """Real Tavily Search with Smart Fallback"""

    def __init__(self, runtime):
        self.runtime = runtime
        self.name = "searcher"
        
        self.api_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.api_url = "https://api.tavily.com/search"
        
        if self.api_key:
            logger.info(f"[{self.name}] ✅ Tavily API Key loaded successfully")
        else:
            logger.warning(f"[{self.name}] ⚠️ TAVILY_API_KEY not found → Using mock fallback")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        queries = task.get("queries", [])
        if not queries:
            return {"sources": [], "status": "error"}

        all_sources = []

        if self.api_key:
            logger.info(f"[{self.name}] 🔍 Using REAL Tavily Search")
            async with aiohttp.ClientSession() as session:
                for query in queries[:3]:   # Limit to 3 queries
                    sources = await self._search_tavily(session, query)
                    all_sources.extend(sources)
        else:
            logger.info(f"[{self.name}] Using mock results (no API key)")
            for query in queries:
                all_sources.extend(self._mock_search(query))

        return {
            "sources": all_sources[:15],
            "total_sources": len(all_sources),
            "status": "success",
            "used_real_search": bool(self.api_key)
        }

    async def _search_tavily(self, session: aiohttp.ClientSession, query: str) -> List[Dict]:
        """Real Tavily API call"""
        sources = []
        payload = {
            "api_key": self.api_key,
            "query": query,
            "include_answer": True,
            "max_results": 8,
            "search_depth": "basic"
        }

        try:
            async with session.post(self.api_url, json=payload, timeout=25) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    # Direct Answer
                    if data.get("answer"):
                        sources.append({
                            "title": "Direct Answer",
                            "content": data["answer"],
                            "url": "tavily_answer",
                            "type": "answer"
                        })

                    # Results
                    for result in data.get("results", []):
                        sources.append({
                            "title": result.get("title", "No Title"),
                            "url": result.get("url", ""),
                            "content": result.get("content", "")[:450],
                            "type": "web_result",
                            "relevance": result.get("score", 0.7)
                        })
                else:
                    logger.error(f"Tavily returned status {resp.status}")
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")

        return sources

    def _mock_search(self, query: str) -> List[Dict]:
        """Fallback mock"""
        if any(k in query.lower() for k in ["russia", "capital", "moscow"]):
            return [
                {"title": "Moscow - Capital of Russia", "url": "https://en.wikipedia.org/wiki/Moscow", "content": "Moscow is the capital and largest city of Russia...", "type": "answer"},
                {"title": "Russia - Wikipedia", "url": "https://en.wikipedia.org/wiki/Russia", "content": "The capital of Russia is Moscow...", "type": "web_result"}
            ]
        return [{"title": f"Results for {query}", "url": "#", "content": "Information retrieved from web sources.", "type": "web_result"}]