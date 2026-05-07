import re
from typing import Dict, Any


class PreprocessorAgent:
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = task.get("prompt", "")

        cleaned = self._clean_prompt(prompt)
        code = self._extract_code(prompt)

        return {
            "original_prompt": prompt,
            "normalized_prompt": cleaned,
            "code": code,
            "has_code": bool(code),
            "task_hint": self._detect_task(prompt)
        }

    def _clean_prompt(self, text: str) -> str:
        if not text:
            return ""

        # normalize whitespace only
        text = text.replace("\r\n", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _extract_code(self, text: str) -> str:
        if not text:
            return ""

        code_markers = (
            "for ",
            "def ",
            "if ",
            "while ",
            "class ",
            "import ",
            "return "
        )

        if any(marker in text for marker in code_markers):
            return text

        return ""

    def _detect_task(self, text: str) -> str:
        t = text.lower()

        if any(x in t for x in ["fix", "error", "debug", "bug", "traceback"]):
            return "debug"

        if any(x in t for x in ["build", "create", "make", "generate"]):
            return "build"

        if any(x in t for x in ["search", "research", "what is", "find"]):
            return "research"

        return "chat"