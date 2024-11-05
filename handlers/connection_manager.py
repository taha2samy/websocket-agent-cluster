# handlers/connection_manager.py
import asyncio
import logging
import uuid
from datetime import datetime
from redis_client import create_redis_connection
from handlers.redis_listener import redis_listener
from handlers.message_handler import handle_message
from handlers.notification_manager import publish_notification

logger = logging.getLogger("WebSocketAgent")

async def process_message(websocket, path, config, db_manager=None):
    headers = websocket.request_headers
    token = headers.get("Authorization")

    # Determine token validation mode
    if 'tokens' in config and config['tokens']:
        token_data = config['tokens'].get(token)
        if not token_data:
            await websocket.close(code=4001, reason="Unauthorized")
            logger.warning("Unauthorized access attempt with token: %s", token)
            return
    elif db_manager:
        token_data = db_manager.check_token(token)
        if token_data is None:
            await websocket.close(code=4001, reason="Unauthorized")
            logger.warning("Unauthorized access attempt with token: %s", token)
            return
    else:
        await websocket.close(code=4001, reason="No token provider configured")
        return
    allowed_tags = token_data["tags"]
    permissions = token_data["permissions"]
    sender_id = str(uuid.uuid4())
    ip_address_my = websocket.remote_address[0]
    user_agent = headers.get("User-Agent")
    ip_address, port = websocket.remote_address
    metadata = {
        "port": port,
        "client_ip_address": ip_address,
        "my_ip_address": ip_address_my,
        "user_agent": user_agent,
        "timestamp": datetime.utcnow().isoformat()
    }

    connection_notification = {
        "action": "connection_status",
        "token": token,
        "uuid": sender_id,
        "status": "accepted",
        "metadata": metadata
    }
    await publish_notification(connection_notification, config)

    client_redis = await create_redis_connection(config['redis'])
    listener_task = asyncio.create_task(redis_listener(websocket, sender_id, allowed_tags, permissions, config))

    try:
        async for message in websocket:
            await handle_message(message, websocket, client_redis, allowed_tags, permissions, sender_id, config)
    except websockets.ConnectionClosedError:
        logger.info("Connection closed by client")
    finally:
        listener_task.cancel()
        await client_redis.close()
        logger.info("Client Redis connection closed")
        disconnection_notification = {
            "action": "connection_status",
            "token": token,
            "uuid": sender_id,
            "status": "closed",
            "metadata": metadata
        }
        await publish_notification(disconnection_notification, config)
