class ChatAgent:
    """
    Smart General Conversation Agent
    Handles general questions intelligently with better responses
    """

    def __init__(self, runtime):
        self.runtime = runtime
        self.name = "chat"

    async def run(self, task):
        prompt = task.get("prompt", "").strip()
        user_id = task.get("user_id", "default_user")

        if not prompt:
            return {
                "agent": "chat",
                "message": "How can I help you today?"
            }

        prompt_lower = prompt.lower()

        # ───── SMART RESPONSES ─────
        if any(word in prompt_lower for word in ["hello", "hi", "hey", "greetings"]):
            return {
                "agent": "chat",
                "message": "Hello! I'm NOX, your AI workspace assistant. How can I help you today?"
            }

        if "how are you" in prompt_lower:
            return {
                "agent": "chat",
                "message": "I'm doing great, thanks for asking! Ready to build, research, or solve problems with you 🚀"
            }

        if "who are you" in prompt_lower or "what are you" in prompt_lower:
            return {
                "agent": "chat",
                "message": "I'm NOX — an intelligent AI workspace powered by multiple specialized agents. I can build apps, research topics, debug code, and more."
            }

        if "time" in prompt_lower:
            from datetime import datetime
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {
                "agent": "chat",
                "message": f"The current time is {now}."
            }

        if "joke" in prompt_lower:
            return {
                "agent": "chat",
                "message": "Why do programmers prefer dark mode? Because light attracts bugs! 😄"
            }

        # Math (simple fallback)
        if any(word in prompt_lower for word in ["sum", "add", "calculate", "+"]) and any(char.isdigit() for char in prompt):
            return {
                "agent": "chat",
                "message": "For calculations, try phrasing it like 'calculate 30000 + 2000' — Lily should route it properly now."
            }

        # Default smart response
        return {
            "agent": "chat",
            "message": f"I understand you're asking about: **{prompt}**\n\nI'll research this properly for you."
        }