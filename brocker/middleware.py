import logging
from channels.middleware import BaseMiddleware
from brocker.check_tags_permissions import check_tags_permissions
from django.core.cache import cache
from brocker.consumers import sanitize_tag

logger = logging.getLogger(__name__)

class AuthMiddlewareBroker(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        token = headers.get(b'authorization', None)
        tags_header = headers.get(b'tag', None)

        token_str = token.decode().split(' ')[1] if token and b' ' in token else token.decode() if token else None
        tags_str = tags_header.decode() if tags_header else None

        if not token_str or not tags_str:
            logger.warning(f"Connection rejected: Missing token or tags. IP: {scope.get('client')}")
            await send({"type": "websocket.close", "code": 4001})
            return

        result = await check_tags_permissions(token_str, tags_str)

        if result is None:
            logger.warning(f"Connection rejected: Invalid token '{token_str}' or tags '{tags_str}'.")
            await send({"type": "websocket.close", "code": 4003})
            return

        tag_permissions, max_connections = result
        
        if max_connections > 0:
            safe_token = sanitize_tag(token_str)
            cache_key = f"connections:{safe_token}"
            current_connections = cache.get(cache_key, 0)
            
            if current_connections >= max_connections:
                logger.warning(
                    "Connection rejected for token %s: Connection limit reached (%s/%s)",
                    token_str, current_connections, max_connections
                )
                await send({"type": "websocket.close", "code": 4004})
                return

        scope['tag_permissions'] = tag_permissions
        scope['max_connections'] = max_connections
        scope['token'] = token_str

        logger.info(f"Connection successful for token '{token_str}' with tags '{tags_str}'.")
        return await super().__call__(scope, receive, send)