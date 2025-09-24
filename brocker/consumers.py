from channels.generic.websocket import AsyncWebsocketConsumer
import json
from brocker.MqttPatternMatcher import MqttPatternMatcher
import re
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

def sanitize_tag(tag):
    tag = str(tag)
    tag = re.sub(r'[^0-9a-zA-Z\-\._]', '_', tag)
    return tag[:100]

class BrokerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("Client connected:", self.scope)
        token = self.scope.get("token")
        max_connections = self.scope.get("max_connections", 0)

        if token and max_connections > 0:
            safe_token = sanitize_tag(token)
            cache_key = f"connections:{safe_token}"
            connection_count = cache.incr(cache_key, 1)
            logger.info(
                "Client connected: token=%s, connections=%s/%s, channel=%s",
                token, connection_count, max_connections, self.channel_name
            )
        else:
            logger.info("Client connected: token=%s, channel=%s", token, self.channel_name)

        for tag in self.scope.get("tag_permissions", {}).keys():
            safe_tag = sanitize_tag(tag)
            await self.channel_layer.group_add(safe_tag, self.channel_name)
        
        if token:
            await self.channel_layer.group_add(f"token_{sanitize_tag(token)}", self.channel_name)

    async def disconnect(self, close_code):
        token = self.scope.get("token")
        max_connections = self.scope.get("max_connections", 0)

        if token and max_connections > 0:
            safe_token = sanitize_tag(token)
            cache_key = f"connections:{safe_token}"
            connection_count = cache.decr(cache_key, 1)
            logger.info(
                "Client disconnected: token=%s, connections=%s/%s, channel=%s, code=%s",
                token, connection_count, max_connections, self.channel_name, close_code
            )
        else:
            logger.info(
                "Client disconnected: token=%s, channel_name=%s, code=%s",
                token, self.channel_name, close_code
            )

        if token:
            await self.channel_layer.group_discard(f"token_{sanitize_tag(token)}", self.channel_name)
        
        for tag in self.scope.get("tag_permissions", {}):
            safe_tag = sanitize_tag(tag)
            await self.channel_layer.group_discard(safe_tag, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        token = self.scope.get("token")
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received from token %s: %s", token, text_data)
            return

        tag = data.get('tag')
        message = data.get('message')

        if not tag or not message:
            logger.debug("Received incomplete message from token %s: %s", token, text_data)
            return

        permissions = self.scope.get('tag_permissions', {})
        if tag in permissions and permissions[tag] == 'readwrite':
            logger.debug("Broadcasting message from token %s to tag '%s'", token, tag)
            safe_tag = sanitize_tag(tag)
            await self.channel_layer.group_send(
                safe_tag,
                {
                    "type": "broadcast_message",
                    "tag": tag,
                    "message": message,
                    "channel": self.channel_name,
                }
            )
        else:
            logger.warning(
                "Write attempt denied for token %s on tag '%s' (permission: %s)",
                token, tag, permissions.get(tag, 'None')
            )

    async def broadcast_message(self, event):
        if event.get('channel') == self.channel_name:
            return
            
        await self.send(text_data=json.dumps({
            "tag": event['tag'],
            "message": event['message'],
        }))

    async def permission_update(self, event):
        token = self.scope.get("token")
        pattern = event.get('pattern')
        permission = event.get('permission')
        matcher = MqttPatternMatcher()
        
        for tag in self.scope.get('tag_permissions', {}).keys():
            if matcher.is_match(tag, [pattern])['match'] and permission not in ["read", "readwrite"]:
                logger.warning(
                    "Closing connection for token %s due to revoked permission on pattern '%s'",
                    token, pattern
                )
                await self.close(code=4001)
                return

    async def token_update(self, event):
        token = self.scope.get("token")
        logger.warning("Closing connection for token %s due to token modification or deletion.", token)
        await self.close(code=4002)
    
    async def tag_update(self, event):
        token = self.scope.get("token")
        old_prefix = event.get('old_prefix')
        matcher = MqttPatternMatcher()

        for tag in self.scope.get("tag_permissions", {}).keys():
            if matcher.is_match(tag, [old_prefix])['match']:
                logger.warning(
                    "Closing connection for token %s due to modification of subscribed tag pattern '%s'",
                    token, old_prefix
                )
                await self.close(code=4003)
                return