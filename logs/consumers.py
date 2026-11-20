from channels.generic.websocket import AsyncJsonWebsocketConsumer
class LogConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user=self.scope.get("user")
        if not user or not user.is_authenticated: await self.close(); return
        await self.channel_layer.group_add("log_updates",self.channel_name); await self.accept()
    async def disconnect(self,code): await self.channel_layer.group_discard("log_updates",self.channel_name)
    async def log_event(self,event): await self.send_json(event["data"])
