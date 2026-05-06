from typing import Optional, List, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
import logging

from nox_backend.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    prompt: Union[str, Dict[str, Any]] = Field(..., description="Prompt or structured payload")
    context: Optional[Dict[str, Any]] = None
    mode: Optional[str] = None


@router.post("/message")
async def chat(
    data: ChatRequest,
    user: str = Depends(get_current_user),
    request: Request = None
):
    """
    Main chat endpoint with full ContentGenerator support
    """
    try:
        # Normalize input
        if isinstance(data.prompt, dict):
            payload = data.prompt
            prompt = payload.get("prompt", "").strip()
            context = payload.get("context", {}) or data.context or {}
            mode = payload.get("mode") or data.mode
        else:
            prompt = str(data.prompt).strip()
            context = data.context or {}
            mode = data.mode

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        user_id = str(user).lower().strip()

        logger.info(f"[CHAT] Processing: {prompt[:80]}... for {user_id}")

        # Engine access
        if not request or not hasattr(request.app.state, "engine"):
            raise HTTPException(status_code=500, detail="Engine not initialized")

        engine = request.app.state.engine
        if engine is None:
            raise HTTPException(status_code=500, detail="Engine is None")

        # Call main engine
        result = await engine.handle_prompt(
            prompt=prompt,
            user_id=user_id,
            context=context,
            mode=mode
        )

        logger.debug(f"[CHAT] Result type: {result.get('type')}, Action: {result.get('action')}")

        # Extract job_id safely
        job_id = None
        if isinstance(result, dict):
            job_id = result.get("job_id") or result.get("data", {}).get("job_id")

        # Handle research results specially
        action = (result.get("action") or "").lower()
        response_type = (result.get("type") or "").lower()
        
        if action == "research" or response_type == "research_result":
            logger.info(f"[CHAT] Returning research result")
            return {
                "response": result.get("response") or result.get("summary") or "Research completed",
                "status": result.get("status", "ok"),
                "type": "research_result",
                "action": "research",
                "research_query": result.get("research_query"),
                "research_type": result.get("research_type"),
                "sources_found": result.get("sources_found", 0),
                "sources": result.get("sources", []),
                "sub_questions": result.get("sub_questions", []),
                "analysis": result.get("analysis", {}),
                "validation": result.get("validation", {}),
                "synthesis": result.get("synthesis", {}),
                "report": result.get("report", {}),
                "data": result,
                "logs": result.get("logs", []),
            }

        # Default response for other actions
        response_dict = {
            "response": result.get("response") or result.get("message") or "✅ Task completed",
            "status": result.get("status", "ok"),
            "type": result.get("type", "message"),
            "action": result.get("action", "chat"),
            "job_id": job_id,
            "data": result.get("data", {}),
            "meta": result.get("meta", {}),
            "updated_files": result.get("updated_files"),
            "diffs": result.get("diffs"),
            "analysis": result.get("analysis"),
            "root_cause": result.get("root_cause"),
            "summary": result.get("summary"),
            "structured": result.get("structured"),
            "chain": result.get("chain"),
            "logs": result.get("logs", []),
        }

        logger.info(f"[CHAT] Response sent | Type: {response_dict['type']} | Job ID: {job_id}")
        return response_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CHAT] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))