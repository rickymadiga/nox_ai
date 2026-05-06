import requests

BASE_URL = "http://localhost:8000/api"

class AgentRouter:

    def route(self, prompt, intent):

        if intent == "fixer":
            res = requests.post(
                f"{BASE_URL}/fixer/analyze",
                json={
                    "prompt": prompt,
                    "error_trace": "",
                    "context": {},
                    "files": {}
                }
            )
            return res.json()

        elif intent == "chat":
            res = requests.post(
                f"{BASE_URL}/chat/message",
                json={"message": prompt}
            )
            return res.json()

        # etc...