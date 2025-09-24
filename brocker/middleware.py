from channels.middleware import BaseMiddleware
from .check_tags_permissions import check_tags_permissions
from channels.generic.websocket import AsyncWebsocketConsumer

class AuthMiddlewareBroker(BaseMiddleware):
    """
    Middleware to validate token and tags before allowing the connection.
    Rejects the connection if the token is invalid or any tag is not allowed,
    using WebSocket close codes (does not raise exceptions).
    """

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        token = headers.get(b'authorization', None)
        tags_header = headers.get(b'tag', None)

        # Convert bytes to string
        token_str = token.decode().split(' ')[1] if token and b' ' in token else token.decode() if token else None
        tags_str = tags_header.decode() if tags_header else None

        # If missing token or tags → reject quietly
        if not token_str or not tags_str:
            await send({
                "type": "websocket.close",
                "code": 4001,  # custom code for invalid auth
            })
            return

        # Check tags and permissions
        result = await check_tags_permissions(token_str, tags_str)

        # Reject if any tag invalid
        if result is None:
            await send({
                "type": "websocket.close",
                "code": 4003,  # custom code for invalid tags
            })
            return

        tag_permissions, max_connections = result

        scope['tag_permissions'] = tag_permissions
        scope['max_connections'] = max_connections
        scope['token'] = token_str

        # All checks passed → allow connection
        return await super().__call__(scope, receive, send)
