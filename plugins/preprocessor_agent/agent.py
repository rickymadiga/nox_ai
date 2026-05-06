# nox/agents/preprocessor_agent.py

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
        noise = ["fix this code", "please", "help me", "can you"]
        t = text.lower()
        for n in noise:
            t = t.replace(n, "")
        return t.strip()

    def _extract_code(self, text: str) -> str:
        # crude but effective v1
        if "for " in text or "def " in text or "if " in text:
            return text
        return ""

    def _detect_task(self, text: str) -> str:
        t = text.lower()
        if "fix" in t or "error" in t:
            return "debug"
        if "build" in t:
            return "build"
        return "chat"