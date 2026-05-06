from fastapi import APIRouter
from fastapi.responses import FileResponse
from nox.core.video_jobs import VideoJobManager
from typing import Dict, Any
import os

router = APIRouter()
video_manager = VideoJobManager()

@router.get("/status/{job_id}")
async def get_video_status(job_id: str) -> Dict[str, Any]:
    """Get the status of a specific video job"""
    status = video_manager.get(job_id)
    
    # If done, include the file path and download URL
    if status.get("status") == "done" and status.get("file_path"):
        return {
            "success": True,
            "job_id": job_id,
            "status": "done",
            "file_path": status["file_path"],
            "download_url": f"/api/video/download/{job_id}",
            "data": status
        }
    
    return {
        "success": True,
        "job_id": job_id,
        "status": status.get("status", "not_found"),
        "data": status
    }

@router.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download generated video file"""
    status = video_manager.get(job_id)
    
    if not status or status.get("status") != "done":
        return {"error": "Video not ready or not found"}
    
    file_path = status.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return {"error": "Video file not found"}
    
    return FileResponse(
        path=file_path,
        filename=f"video_{job_id}.mp4",
        media_type="video/mp4"
    )

@router.get("/jobs")
async def get_all_video_jobs():
    """Get all video jobs"""
    return {
        "success": True,
        "total": len(video_manager.jobs),
        "jobs": video_manager.jobs
    }