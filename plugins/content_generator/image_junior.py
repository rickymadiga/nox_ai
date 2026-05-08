from typing import Dict, Any
from openai import OpenAI
from .base_junior import BaseJunior

# Initialize OpenAI client once at module level
client = OpenAI()

class ImageJunior(BaseJunior):

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = data.get("prompt", "")
        original_prompt = data.get("original_prompt", prompt)
        research_context = data.get("research_context", "")
        key_findings = data.get("key_findings", [])

        try:
            # ───── ENRICH PROMPT WITH RESEARCH ─────
            if research_context and len(research_context) > 30:
                enriched_prompt = f"""
                {original_prompt}

                Create a highly detailed, accurate, and visually stunning image using this researched information:

                {research_context}

                Key elements to include:
                {', '.join(key_findings[:8])}
                """.strip()
                
                final_prompt = enriched_prompt
                used_research = True
            else:
                final_prompt = prompt
                used_research = False

            # Generate image using OpenAI
            result = client.images.generate(
                model="gpt-image-1",           # or "dall-e-3"
                prompt=final_prompt,
                size="1024x1024",
                quality="standard",            # or "hd"
                n=1
            )

            image_url = result.data[0].url

            return {
                "status": "ok",
                "type": "image",
                "data": {
                    "url": image_url,
                    "prompt": original_prompt,
                    "research_used": used_research
                },
                "meta": {
                    "message": "Image generated successfully" + (" with research context" if used_research else ""),
                    "research_enhanced": used_research
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "type": "image",
                "data": {},
                "meta": {
                    "error": str(e)
                }
            }