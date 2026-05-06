import time

async def activity_listener(event, ws_manager):
    await ws_manager.send_to_user(
        event.user_id,
        {
            "type": "activity",
            "message": event.message,
            "timestamp": time.time()
        }
    )