from typing import Dict, Any
from .base_junior import BaseJunior

class EditorJunior(BaseJunior):

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        content = data.get("content", "")

        # Simple cleaning
        edited = content.replace("  ", " ").strip()

        return {
            "status": "ok",
            "type": "text",
            "data": {
                "edited_content": edited
            },
            "meta": {}
        }