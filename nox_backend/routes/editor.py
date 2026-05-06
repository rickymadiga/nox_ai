from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from nox_backend.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["editor"])


@router.post("/edit")
async def edit_code(payload: dict, request: Request):
    engine = request.app.state.engine

    result = await engine.execute_agent(
        "code_assistant",
        {
            "prompt": payload.get("instruction"),
            "user_id": payload.get("user_id", "default_user"),
            "context": {
                "mode_override": "fixer",  # 👈 force fixer mode
                "inline": True,
                "file": payload.get("file"),
                "selection": payload.get("selection"),
            }
        }
    )

    updated_files = result.get("updated_files", {})
    diffs = result.get("diffs", {})

    # Return first file for editor
    file = payload.get("file")

    return {
        "updated_code": updated_files.get(file),
        "patch": diffs.get(file),
        "all_files": updated_files
    }