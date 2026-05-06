import os
import sqlite3
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from nox_backend.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/download/latest")  # ✅ Changed from /latest to /download/latest
async def download_latest(user: str = Depends(get_current_user), request: Request = None):
    """Download the latest build ZIP for a user"""
    try:
        user_id = str(user).lower().strip()
        logger.info(f"[DOWNLOAD] Fetching latest ZIP for {user_id}")
        
        # Get from runtime
        last_zip = getattr(request.app.state.engine.runtime, "last_zip", {})
        zip_data = last_zip.get(user_id)

        if zip_data and zip_data.get("path") and os.path.exists(zip_data["path"]):
            return FileResponse(
                path=zip_data["path"],
                filename=zip_data.get("filename", "nox_app.zip"),
                media_type="application/zip"
            )

        # Fallback to generated_apps directory
        try:
            if os.path.exists("generated_apps"):
                files = [f for f in os.listdir("generated_apps") if f.endswith(".zip")]
                if files:
                    files.sort(
                        key=lambda x: os.path.getmtime(os.path.join("generated_apps", x)),
                        reverse=True
                    )
                    latest_file = files[0]
                    latest_path = os.path.join("generated_apps", latest_file)
                    logger.info(f"[DOWNLOAD] Serving: {latest_file}")
                    return FileResponse(
                        path=latest_path,
                        filename=latest_file,
                        media_type="application/zip"
                    )
        except Exception as e:
            logger.warning(f"[DOWNLOAD] Fallback error: {e}")

        logger.error(f"[DOWNLOAD] No build found for {user_id}")
        raise HTTPException(status_code=404, detail="No build available")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DOWNLOAD] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Download failed")


@router.get("/download/{build_id}")
async def download_build(build_id: str, user: str = Depends(get_current_user), request: Request = None):
    """Download a specific build by ID"""
    try:
        user_id = str(user).lower().strip()
        logger.info(f"[DOWNLOAD] Fetching build {build_id} for {user_id}")
        
        with sqlite3.connect("builds.db") as conn:
            row = conn.execute(
                "SELECT path, filename FROM builds WHERE id=? AND user_id=?",
                (build_id, user_id)
            ).fetchone()

        if not row:
            logger.warning(f"[DOWNLOAD] Build {build_id} not found")
            raise HTTPException(status_code=404, detail="Build not found")

        path, filename = row

        if not os.path.exists(path):
            logger.error(f"[DOWNLOAD] File missing: {path}")
            raise HTTPException(status_code=404, detail="File missing")

        logger.info(f"[DOWNLOAD] Serving: {filename}")
        return FileResponse(
            path=path,
            filename=filename,
            media_type="application/zip"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DOWNLOAD] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))