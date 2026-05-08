import asyncio
from typing import Dict, Any
from .base_junior import BaseJunior
from nox.core.video_jobs import video_manager   # global instance

class VideoJunior(BaseJunior):

    def __init__(self, job_manager=None):
        self.job_manager = job_manager or video_manager

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = data.get("prompt", "")
        original_prompt = data.get("original_prompt", prompt)
        research_context = data.get("research_context", "")
        key_findings = data.get("key_findings", [])

        if not self.job_manager:
            return {
                "status": "error",
                "type": "video",
                "data": {"error": "No job_manager available"},
                "meta": {"error": "VideoJunior has no job_manager"}
            }

        try:
            # ───── BUILD ENRICHED PROMPT FOR BETTER VIDEO ─────
            if research_context and len(research_context) > 20:
                enriched_prompt = f"""
                {original_prompt}

                Create an engaging, accurate, and informative video using the following researched information:

                {research_context}

                Important Points to Highlight:
                {chr(10).join([f"• {fact}" for fact in key_findings[:10]])}
                """.strip()
                
                final_prompt = enriched_prompt
                used_research = True
            else:
                final_prompt = prompt
                used_research = False

            # Submit to video manager
            job_id = await self.job_manager.submit(final_prompt)

            self.runtime.add_log(  # assuming runtime is available via BaseJunior
                data.get("user_id", "default"), 
                f"🎬 Video job submitted with research: {used_research}"
            )

            await asyncio.sleep(1)  # Brief wait for job to register

            return {
                "status": "processing",
                "type": "video",
                "data": {
                    "job_id": job_id,
                    "prompt": original_prompt[:150] + "..." if len(original_prompt) > 150 else original_prompt,
                    "research_used": used_research,
                    "research_summary": research_context[:250] + "..." if research_context else None
                },
                "meta": {
                    "message": "Video generation started with research context" if used_research else "Video generation started",
                    "estimated_time": "30-90 seconds",
                    "research_enhanced": used_research
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "type": "video",
                "data": {},
                "meta": {"error": str(e)}
            }