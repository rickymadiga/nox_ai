from typing import Dict, Any
from .base_junior import BaseJunior

class QualityReviewerJunior(BaseJunior):
    """
    Advanced quality review junior that evaluates content quality 
    across multiple dimensions and provides improvement suggestions.
    """

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        content = data.get("content", "").strip()
        content_type = data.get("type", "text")  # text, image_prompt, video_script, etc.

        if not content:
            return {
                "status": "error",
                "quality_score": 0,
                "approved": False,
                "meta": {"error": "No content provided for review"}
            }

        # === Quality Analysis ===
        length = len(content)
        word_count = len(content.split())

        # Basic scoring factors
        score = 60  # base score

        # Length evaluation
        if content_type == "text":
            if 300 <= length <= 2500:
                score += 15
            elif length > 2500:
                score += 8   # too long
            elif length < 100:
                score -= 10  # too short

        # Readability & Structure
        if "." in content and len(content.split('.')) >= 3:
            score += 10
        if any(marker in content.lower() for marker in ["however", "therefore", "additionally", "finally"]):
            score += 8

        # Engagement & Vocabulary
        engaging_words = ["amazing", "incredible", "transform", "discover", "secret", "ultimate"]
        if any(word in content.lower() for word in engaging_words):
            score += 7

        # Cap the score
        score = min(98, max(40, score))

        approved = score >= 75

        suggestions = []
        if length < 150 and content_type == "text":
            suggestions.append("Content is quite short. Consider adding more details or examples.")
        if length > 3000 and content_type == "text":
            suggestions.append("Content is very long. Consider breaking it into sections.")
        if "." not in content or len(content.split('.')) < 3:
            suggestions.append("Add more sentences and proper paragraph structure.")

        return {
            "status": "ok",
            "type": "quality_review",
            "quality_score": round(score, 1),
            "approved": approved,
            "word_count": word_count,
            "character_count": length,
            "suggestions": suggestions,
            "meta": {
                "reviewer": "QualityReviewerJunior",
                "content_type": content_type,
                "strengths": self._get_strengths(content)
            }
        }

    def _get_strengths(self, content: str) -> list:
        """Identify strengths in the content"""
        strengths = []
        lower = content.lower()
        if len([c for c in lower if c in "?!"]) > 2:
            strengths.append("Good use of emotional punctuation")
        if any(word in lower for word in ["because", "since", "due to"]):
            strengths.append("Uses causal reasoning")
        return strengths