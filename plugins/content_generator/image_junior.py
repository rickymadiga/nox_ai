from typing import Dict, Any
from openai import OpenAI
from .base_junior import BaseJunior

# Initialize OpenAI client once at module level
client = OpenAI()

class ImageJunior(BaseJunior):

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = data.get("prompt", "")

        try:
            result = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024"
            )

            return {
                "status": "ok",
                "type": "image",
                "data": {
                    "url": result.data[0].url
                },
                "meta": {}
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