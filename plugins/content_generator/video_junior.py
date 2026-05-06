import asyncio
from typing import Dict, Any
from .base_junior import BaseJunior
from nox.core.video_jobs import video_manager   # global instance

class VideoJunior(BaseJunior):

    def __init__(self, job_manager=None):
        self.job_manager = job_manager or video_manager

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = data.get("prompt", "")

        if not self.job_manager:
            return {
                "status": "error",
                "type": "video",
                "data": {"error": "No job_manager available"},
                "meta": {"error": "VideoJunior has no job_manager"}
            }

        try:
            job_id = await self.job_manager.submit(prompt)
        
            # Wait for video generation (with timeout)
            await asyncio.sleep(1)  # Brief wait for processing to start
        
            return {
                "status": "processing",
                "type": "video",
                "data": {
                    "job_id": job_id,
                    "prompt": prompt[:150] + "..." if len(prompt) > 150 else prompt
                },
                "meta": {
                    "message": "Video job queued successfully",
                   "estimated_time": "5-10 seconds"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "type": "video",
                "data": {},
            "meta": {"error": str(e)}
          }