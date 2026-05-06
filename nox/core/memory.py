class Memory:
    def __init__(self):
        self.store = {}

    def save(self, key, value):
        self.store[key] = value

    def load(self, key):
        return self.store.get(key)
    

from typing import Dict, List, Any

class InMemoryHistoryStore:
    def __init__(self):
        self.history: Dict[str, List[Dict[str, Any]]] = {}

    def add_message(self, session_id: str, message: Dict[str, Any]):
        if session_id not in self.history:
            self.history[session_id] = []
        self.history[session_id].append(message)

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self.history.get(session_id, [])

    def clear(self, session_id: str):
        if session_id in self.history:
            del self.history[session_id]    