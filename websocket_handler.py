import asyncio
import json
import uuid
import xml.etree.ElementTree as ET
import websockets
from redis_client import create_redis_connection
from sqlite_manager import SQLiteManager
import logging
from datetime import datetime

logger = logging.getLogger("WebSocketAgent")

async def redis_listener(websocket, sender_id, allowed_tags, permissions, config):
    client_redis = await create_redis_connection(config['redis'])  # Separate connection for redis_listener
    pubsub = client_redis.pubsub()
    await pubsub.subscribe(*[f"{config['redis']['channel_prefix']}{tag}" for tag in allowed_tags])

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                message_data = json.loads(message["data"].decode("utf-8"))
                if message_data.get("sender_id") != sender_id:
                    tag_name = message["channel"].decode("utf-8").replace(config['redis']['channel_prefix'], "")
                    if permissions.get(tag_name, {}).get("receive"):
                        await websocket.send(json.dumps({"tag": tag_name, "data": message_data["content"]}))
                        logger.debug(f"Message sent to WebSocket client on tag {tag_name}: {message_data['content']}")
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"Error in redis_listener: {e}")
    finally:
        await pubsub.unsubscribe(*allowed_tags)
        await client_redis.close()

async def handle_message(message, websocket, client_redis, allowed_tags, permissions, sender_id, config):
    if "json" in config['message_type']:
        try:
            message_data = json.loads(message)
            tags = message_data.get("tag")
            target_tags = tags.split(",") if tags else allowed_tags
        except:
            target_tags = allowed_tags
            logger.error("Invalid JSON message format")
    elif config['message_type'] == "xml":
        try:
            root = ET.fromstring(message)
            tags_element = root.find("tag")
            target_tags = tags_element.text.split(",") if tags_element is not None else allowed_tags
        except:
            target_tags = allowed_tags
            logger.error("Invalid XML message format")
    else:
        target_tags = allowed_tags

    logger.debug(f"Target tags for message: {target_tags}")

    for tag in target_tags:
        if tag in allowed_tags and permissions.get(tag, {}).get("send"):
            redis_channel = f"{config['redis']['channel_prefix']}{tag}"
            payload = json.dumps({"sender_id": sender_id, "content": message})
            await client_redis.publish(redis_channel, payload)
            logger.debug(f"Published message to Redis channel {redis_channel}: {message}")
        else:
            logger.warning(f"Send permission denied for tag {tag}")

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

    # Notify about the new connection
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

async def publish_notification(notification, config):
    client_redis = await create_redis_connection(config['redis'])
    channel = f"{config['server']['comands_metadata']}"
    await client_redis.publish(channel, json.dumps(notification))
    await client_redis.close()

async def commands_listener(config):
    client_redis = await create_redis_connection(config['redis'])  # Separate connection for commands_listener
    pubsub = client_redis.pubsub()
    await pubsub.subscribe(config['server']['comands_metadata'])

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                command_data = json.loads(message["data"].decode("utf-8"))
                command = command_data.get("command")
                target_uuid = command_data.get("uuid")
                target_token = command_data.get("token")
                
                if command == "shutdown":
                    for uuid, connection_info in active_connections.items():
                        await connection_info["websocket"].close(code=4002, reason="Server shutdown command received")
                        logger.info(f"Shutdown command received; closed connection with UUID: {uuid}.")
                    break
                elif command == "close_connection_by_uuid" and target_uuid:
                    connection_info = active_connections.get(target_uuid)
                    if connection_info:
                        await connection_info["websocket"].close(code=4003, reason="Close connection by UUID command received")
                        logger.info(f"Close connection by UUID command received; closed connection with UUID: {target_uuid}.")
                        del active_connections[target_uuid]
                elif command == "close_connection_by_token" and target_token:
                    to_close = [uuid for uuid, conn in active_connections.items() if conn["token"] == target_token]
                    for uuid in to_close:
                        await active_connections[uuid]["websocket"].close(code=4004, reason="Close connection by token command received")
                        logger.info(f"Close connection by token command received; closed connection with Token: {target_token} and UUID: {uuid}.")
                        del active_connections[uuid]
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"Error in commands_listener: {e}")
    finally:
        await pubsub.unsubscribe()
        await client_redis.close()
