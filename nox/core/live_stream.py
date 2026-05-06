class LiveActivityBridge:

    def __init__(self, runtime, ws_manager):
        self.runtime = runtime
        self.ws_manager = ws_manager

        # subscribe to ALL activity events
        self.runtime.bus.subscribe("activity", self.handle_activity)

    async def handle_activity(self, message):

        user_id = message.get("user_id")
        if not user_id:
            return

        await self.ws_manager.send_to_user(user_id, {
            "type": "activity",
            "message": message.get("message"),
        })