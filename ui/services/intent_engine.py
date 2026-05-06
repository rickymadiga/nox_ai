# services/intent_engine.py

class IntentEngine:
    def detect(self, text: str) -> str:
        text = text.lower()

        if any(word in text for word in ["error", "bug", "fix", "crash"]):
            return "fixer"

        if any(word in text for word in ["build", "create", "generate"]):
            return "builder"

        if any(word in text for word in ["research", "find", "search"]):
            return "research"

        return "chat"