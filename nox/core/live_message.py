# core/live_message.py

def normalize_message(message):
    return {
        "type": getattr(message, "message_type", "unknown"),
        "user_id": str(getattr(message, "user_id", "")).lower().strip(),
        "message": getattr(message, "message", str(message)),
        "timestamp": getattr(message, "timestamp", None),
    }