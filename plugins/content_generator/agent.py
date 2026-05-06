from typing import Dict, Any
import asyncio

from .base_junior import BaseJunior
from .editor_junior import EditorJunior
from .image_junior import ImageJunior
from .video_junior import VideoJunior
from .quality_reviewer import QualityReviewerJunior

class ContentGeneratorAgent:

    def __init__(self, runtime, video_manager=None):
        self.runtime = runtime
        self.video_manager = video_manager

        self.juniors = {
            "text": EditorJunior(),
            "image": ImageJunior(),
            "video": VideoJunior(job_manager=self.video_manager),
            "review": QualityReviewerJunior()
        }

    def detect_type(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if any(k in prompt_lower for k in ["review", "quality", "evaluate", "rate this"]):
            return "review"
        if any(k in prompt_lower for k in ["image", "photo", "picture", "draw"]):
            return "image"
        if any(k in prompt_lower for k in ["video", "clip", "animation", "generate video"]):
            return "video"
        return "text"

    async def run(self, task: Any) -> Dict[str, Any]:
        if isinstance(task, dict):
            prompt = task.get("prompt", "")
        else:
            prompt = getattr(task, "prompt", "")

        if not prompt:
            return {"agent": "content_generator", "status": "error", "message": "No prompt provided"}

        content_type = self.detect_type(prompt)
        junior = self.juniors.get(content_type)

        if not junior:
            return {"agent": "content_generator", "status": "error", "message": f"No junior for {content_type}"}

        result = await junior.execute({
            "prompt": prompt,
            "content": prompt,
            "type": content_type
        })

        if content_type == "video":
            job_id = result.get("data", {}).get("job_id")
            if job_id and self.video_manager:
                # Poll for completion (with timeout)
                max_wait = 30
                elapsed = 0
                while elapsed < max_wait:
                    await asyncio.sleep(2)
                    job_status = self.video_manager.get(job_id)
                    elapsed += 2
            
                    if job_status.get("status") == "done":
                        file_path = job_status.get("file_path")
                        return {
                            "agent": "content_generator",
                            "status": "done",
                            "type": "video",
                            "message": "🎬 Video generated successfully!",
                            "job_id": job_id,
                            "data": {
                                "job_id": job_id,
                                "file_path": file_path,
                                "download_url": f"/api/video/download/{job_id}",
                                "prompt": prompt
                            }
                        }
        
                # Timeout
                return {
                    "agent": "content_generator",
                    "status": "processing",
                    "type": "video",
                    "message": "🎬 Video generation in progress...",
                    "job_id": job_id,
                    "data": result.get("data", {})
                }