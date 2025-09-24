from channels.generic.websocket import AsyncWebsocketConsumer
import json
from brocker.MqttPatternMatcher import MqttPatternMatcher
import re

def sanitize_tag(tag):
    """
    Convert tag to a safe group name:
    - Keep only ASCII letters, numbers, -, _, .
    - Replace any other character with underscore
    - Truncate to 100 characters (Channels limit)
    """
    tag = str(tag)
    tag = re.sub(r'[^0-9a-zA-Z\-\._]', '_', tag)
    return tag[:100]

class BrokerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Accept the WebSocket connection and subscribe to all allowed tag groups.
        """
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected!"}))

        # Subscribe to all allowed tag groups
        for tag in self.scope.get("tag_permissions", {}).keys():
            safe_tag = sanitize_tag(tag)
            await self.channel_layer.group_add(safe_tag, self.channel_name)
        await self.channel_layer.group_add(f"token_{sanitize_tag(self.scope.get('token'))}", self.channel_name)

    async def disconnect(self, close_code):
        token = self.scope.get("token")
        if token:
            await self.channel_layer.group_discard(f"token_{sanitize_tag(self.scope.get('token'))}", self.channel_name)
        for tag in self.scope.get("tag_permissions", {}):
            safe_tag = sanitize_tag(tag)
            await self.channel_layer.group_discard(safe_tag, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle messages from the WebSocket client.
        Expects JSON:
        {
            "tags": "tag1,tag2,...",
            "message": "..."
        }
        Only send messages to tags with 'readwrite' permission.
        """
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            # Invalid JSON → ignore
            return

        tag = data.get('tag', '')
        message = data.get('message', '')
        if not tag or not message:
            return


        if tag in self.scope.get('tag_permissions', {}) and \
            self.scope['tag_permissions'][tag] == 'readwrite':
            safe_tag = sanitize_tag(tag)
            await self.channel_layer.group_send(
                safe_tag,
                {
                    "type": "broadcast_message",
                    "tag": tag,
                    "message": message,
                    "channel" : self.channel_name,
                }
            )

    async def broadcast_message(self, event):
        """
        Receive a message from the group and send it to the WebSocket client.
        """
        if event['channel'] == self.channel_name:
            return
        await self.send(text_data=json.dumps({
            "tag": event['tag'],
            "message": event['message'],
        }))
    async def permission_update(self, event):
        pattern = event['pattern']
        permission = event['permission']

        matcher = MqttPatternMatcher()
        tags_to_check = list(self.scope.get('tag_permissions', {}).keys())

        should_disconnect = False

        for tag in tags_to_check:
            if matcher.is_match(tag, [pattern])['match']:
                if permission not in ["read", "readwrite"]:
                    should_disconnect = True
                    break

        if should_disconnect:
            await self.close(code=4001)  
    
    async def token_update(self, event):
        await self.close(code=4002)
    
    async def tag_update(self, event):
        old_prefix = event['old_prefix']
        from brocker.MqttPatternMatcher import MqttPatternMatcher
        matcher = MqttPatternMatcher()

        disconnect = False
        for tag in list(self.scope.get("tag_permissions", {}).keys()):
            if matcher.is_match(tag, [old_prefix])['match']:
                disconnect = True
                break

        if disconnect:
            await self.close(code=4003)  
