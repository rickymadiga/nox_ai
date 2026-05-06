import aiohttp
import os
import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class WebSearcherAgent:
    """Search the web using Tavily API"""

    def __init__(self, runtime):
        self.runtime = runtime
        
        # Get API key from environment
        self.api_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.api_url = "https://api.tavily.com/search"
        self.name = "searcher"
        
        # Debug logging
        print(f"[{self.name}] Initializing...")
        print(f"[{self.name}] API Key exists: {bool(self.api_key)}")
        print(f"[{self.name}] API Key preview: {self.api_key[:30] if self.api_key else 'EMPTY'}...")
        
        if self.api_key:
            logger.info(f"[{self.name}] ✅ TAVILY_API_KEY loaded successfully")
        else:
            logger.error(f"[{self.name}] ❌ TAVILY_API_KEY is EMPTY or NOT SET!")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web search"""
        
        queries = task.get("queries", [])
        
        if not queries:
            logger.warning(f"[{self.name}] No queries provided")
            return {"sources": [], "status": "error", "total_sources": 0}
        
        if not self.api_key:
            logger.error(f"[{self.name}] API key is missing!")
            return {
                "sources": [], 
                "status": "error", 
                "total_sources": 0,
                "error": "TAVILY_API_KEY not configured"
            }
        
        logger.info(f"[{self.name}] Searching {len(queries)} queries with API key: {self.api_key[:20]}...")
        
        all_sources = []
        async with aiohttp.ClientSession() as session:
            for query in queries:
                sources = await self._search_query(session, query)
                all_sources.extend(sources)
                logger.info(f"[{self.name}] Query '{query[:40]}' returned {len(sources)} sources")
        
        logger.info(f"[{self.name}] ✅ Total {len(all_sources)} sources found")
        
        return {
            "sources": all_sources,
            "total_sources": len(all_sources),
            "queries": queries,
            "status": "success"
        }

    async def _search_query(self, session: aiohttp.ClientSession, query: str) -> List[Dict]:
        """Search single query"""
        sources = []
        payload = {
            "api_key": self.api_key,
            "query": query,
            "include_answer": True,
            "max_results": 5,
            "search_depth": "advanced"
        }
        
        try:
            logger.debug(f"[{self.name}] POST to {self.api_url}")
            logger.debug(f"[{self.name}] Payload: query='{query}', api_key_len={len(self.api_key)}")
            
            async with session.post(
                self.api_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                logger.info(f"[{self.name}] Response status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Direct answer
                    if data.get("answer"):
                        sources.append({
                            "title": f"Direct Answer: {query}",
                            "content": data.get("answer"),
                            "url": "direct_answer",
                            "type": "direct_answer",
                            "relevance": 1.0
                        })
                        logger.info(f"[{self.name}] ✅ Got direct answer")
                    
                    # Search results
                    for result in data.get("results", []):
                        sources.append({
                            "title": result.get("title", "Unknown"),
                            "url": result.get("url", ""),
                            "content": result.get("content", "")[:300],
                            "type": "search_result",
                            "relevance": result.get("score", 0.5)
                        })
                    
                    logger.info(f"[{self.name}] ✅ Got {len(sources)} sources from API")
                else:
                    error_text = await resp.text()
                    logger.error(f"[{self.name}] API error {resp.status}: {error_text[:200]}")
                    
        except asyncio.TimeoutError:
            logger.error(f"[{self.name}] Request timeout for query: {query}")
        except Exception as e:
            logger.error(f"[{self.name}] Exception: {type(e).__name__}: {e}", exc_info=True)
        
        return sources