# handlers/connection_manager.py

import asyncio
import logging
import uuid
import websockets
from datetime import datetime

from handlers.redis_listener import redis_listener
from handlers.message_handler import handle_message
from handlers.notification_manager import publish_notification
#from handlers.single_private_key_handler import validate_single_private_key
from handlers.logger import logger

async def manage_client_session(websocket, config, db_manager, active_connections, connection_id, redis_publisher, redis_subscriber):
    """
    Handles the entire lifecycle of a single client connection, from authentication to disconnection.
    """
    headers = websocket.request_headers
    token = headers.get("Authorization")

    # --- Authentication Logic ---
    token_data = None
    if config['mode'] == 'config':
        token_data = config['tokens'].get(token)
    elif config['mode'] == 'sql' and db_manager:
        token_data = db_manager.check_token(token)
    elif config['mode'] == 'single_private_key':
        pass
    if not token_data:
        await websocket.close(code=4001, reason="Unauthorized")
        logger.warning(f"Unauthorized access attempt with token: {token} from {websocket.remote_address[0]}")
        return

    allowed_tags = token_data.get("tags", [])
    permissions = token_data.get("permissions", {})

    # --- Add connection to the shared active_connections dictionary ---
    active_connections[connection_id] = {
        "websocket": websocket,
        "token": token,
        "tags": allowed_tags,
        "permissions": permissions,
        "ip": websocket.remote_address[0]
    }
    logger.info(f"Connection {connection_id} authenticated and registered. Total active: {len(active_connections)}")

    # --- Publish connection notification ---
    metadata = {
        "port": websocket.remote_address[1],
        "client_ip_address": websocket.remote_address[0],
        "user_agent": headers.get("User-Agent"),
        "timestamp": datetime.utcnow().isoformat()
    }
    connection_notification = {
        "action": "connection_status",
        "token": token,
        "uuid": connection_id,
        "status": "accepted",
        "metadata": metadata
    }
    await publish_notification(connection_notification, config, redis_publisher)

    # --- Start the Redis listener for this client ---
    listener_task = asyncio.create_task(
        redis_listener(websocket, connection_id, allowed_tags, permissions, config, redis_subscriber)
    )

    try:
        # --- Main loop to handle incoming messages from this client ---
        async for message in websocket:
            await handle_message(message, allowed_tags, permissions, connection_id, config, redis_publisher)
    except websockets.ConnectionClosedError:
        logger.info(f"Connection {connection_id} closed by client.")
    except Exception as e:
        logger.error(f"Error during client session for {connection_id}: {e}", exc_info=True)
    finally:
        listener_task.cancel()
        logger.info(f"Client session ended for {connection_id}.")
        # --- Publish disconnection notification ---
        disconnection_notification = {
            "action": "connection_status",
            "token": token,
            "uuid": connection_id,
            "status": "closed",
            "metadata": metadata
        }
        await publish_notification(disconnection_notification, config, redis_publisher)