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
        if any(k in prompt_lower for k in ["image", "photo", "picture", "draw", "generate image"]):
            return "image"
        if any(k in prompt_lower for k in ["video", "clip", "animation", "generate video"]):
            return "video"
        return "text"

    async def run(self, task: Any) -> Dict[str, Any]:
        if isinstance(task, dict):
            prompt = task.get("prompt", "")
            enriched_prompt = task.get("enriched_prompt")
            research_context = task.get("research_context", "")
            key_findings = task.get("key_findings", [])
            user_id = task.get("user_id", "default_user")
            content_type = task.get("content_type") or self.detect_type(prompt)
        else:
            prompt = getattr(task, "prompt", "")
            enriched_prompt = None
            research_context = ""
            key_findings = []
            user_id = "default_user"
            content_type = self.detect_type(prompt)

        if not prompt:
            return {"agent": "content_generator", "status": "error", "message": "No prompt provided"}

        self.runtime.add_log(user_id, f"🎨 Content Generator → {content_type} mode")

        # ───── ENRICH PROMPT IF RESEARCH IS AVAILABLE ─────
        if research_context and len(research_context) > 30:
            final_prompt = enriched_prompt or f"""
            {prompt}

            Use the following researched information to create accurate and high-quality content:

            {research_context}

            Key Facts:
            {chr(10).join([f"• {fact}" for fact in key_findings[:10]])}
            """.strip()
            
            used_research = True
            self.runtime.add_log(user_id, f"🔬 Research context integrated for {content_type}")
        else:
            final_prompt = prompt
            used_research = False

        junior = self.juniors.get(content_type)
        if not junior:
            return {"agent": "content_generator", "status": "error", "message": f"No junior for {content_type}"}

        # Execute junior with full context
        result = await junior.execute({
            "prompt": final_prompt,
            "original_prompt": prompt,
            "content": final_prompt,
            "type": content_type,
            "research_context": research_context,
            "key_findings": key_findings,
            "user_id": user_id,
            "used_research": used_research
        })

        # ───── FINAL RESPONSE ─────
        if content_type == "video":
            return {
                "agent": "content_generator",
                "status": result.get("status", "processing"),
                "type": "video",
                "message": "🎬 Video generation started" + (" with research" if used_research else ""),
                "job_id": result.get("data", {}).get("job_id"),
                "research_used": used_research,
                "data": result.get("data", {})
            }
        elif content_type == "image":
            return {
                "agent": "content_generator",
                "status": "success",
                "type": "image",
                "message": "🖼️ Image generated" + (" with research context" if used_research else ""),
                "data": result.get("data", {}),
                "research_used": used_research
            }
        else:
            return {
                "agent": "content_generator",
                "status": "success",
                "type": content_type,
                "message": f"✅ {content_type.capitalize()} generated successfully",
                "data": result.get("data", result),
                "research_used": used_research
            }