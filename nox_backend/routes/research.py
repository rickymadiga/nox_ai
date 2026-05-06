from fastapi import APIRouter, Depends, HTTPException, Request
import logging
from nox_backend.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/research")
async def conduct_research(
    prompt: str,
    research_type: str = "general",
    user: str = Depends(get_current_user),
    request: Request = None
):
    """Conduct research using ResearchAgent"""
    try:
        if not request or not hasattr(request.app.state, "engine"):
            raise HTTPException(status_code=500, detail="Engine not initialized")
        
        engine = request.app.state.engine
        
        user_id = str(user).lower().strip()
        logger.info(f"[RESEARCH] Query: {prompt[:50]} by {user_id}")
        
        # Use engine to execute research agent
        result = await engine.execute_agent("research_agent", {
            "prompt": prompt,
            "user_id": user_id,
            "research_type": research_type
        })
        
        if not result:
            raise HTTPException(status_code=500, detail="Research agent returned no result")
        
        logger.info(f"[RESEARCH] Status: {result.get('status')}, Sources: {result.get('sources_found', 0)}")
        
        return {
            "status": "success",
            "action": "research",
            "type": "research_result",
            "response": result.get("response") or result.get("summary") or "Research completed",
            "research_query": result.get("research_query"),
            "research_type": result.get("research_type"),
            "sub_questions": result.get("sub_questions", []),
            "sources_found": result.get("sources_found", 0),
            "sources": result.get("sources", []),
            "analysis": result.get("analysis", {}),
            "validation": result.get("validation", {}),
            "synthesis": result.get("synthesis", {}),
            "report": result.get("report", {}),
            "data": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RESEARCH] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@router.get("/research/history/{user_id}")
async def get_research_history(
    user_id: str,
    limit: int = 10,
    user: str = Depends(get_current_user),
    request: Request = None
):
    """Get user's research history"""
    try:
        if not request or not hasattr(request.app.state, "engine"):
            raise HTTPException(status_code=500, detail="Engine not initialized")
        
        engine = request.app.state.engine
        
        stats_user_id = str(user_id).lower().strip()
        
        # Permission check
        if user != stats_user_id and user != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get history from memory
        history = []
        if hasattr(engine, "memory") and hasattr(engine.memory, "get_history"):
            history = engine.memory.get_history(stats_user_id)
        
        research_queries = [
            h for h in history 
            if isinstance(h, dict) and h.get("type") == "research"
        ]
        
        logger.info(f"[RESEARCH-HISTORY] Retrieved {len(research_queries)} for {stats_user_id}")
        
        return {
            "status": "success",
            "research_queries": research_queries[-limit:],
            "total": len(research_queries)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RESEARCH-HISTORY] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))