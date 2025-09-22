# handlers/redis_listener.py

import asyncio
import json
import logging

logger = logging.getLogger("WebSocketAgent")

async def redis_listener(websocket, sender_id, allowed_tags, permissions, config, redis_subscriber):
    """Listens on Redis PubSub channels and forwards messages to the WebSocket client."""
    if not allowed_tags:
        logger.warning(f"No tags to listen on for client {sender_id}. Listener will not start.")
        return

    channels = [f"{config['redis']['channel_prefix']}{tag}" for tag in allowed_tags if permissions.get(tag, {}).get("receive", False)]
    if not channels:
        logger.warning(f"Client {sender_id} has no 'receive' permissions for any tags. Listener will not start.")
        return

    pubsub = redis_subscriber.pubsub()
    await pubsub.subscribe(*channels)
    logger.info(f"Client {sender_id} subscribed to Redis channels: {channels}")

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                try:
                    message_data = json.loads(message["data"].decode("utf-8"))
                    # Do not send the message back to the original sender
                    if message_data.get("sender_id") != sender_id:
                        tag_name = message["channel"].decode("utf-8").replace(config['redis']['channel_prefix'], "")
                        # Final permission check before sending
                        if permissions.get(tag_name, {}).get("receive", False):
                            await websocket.send(json.dumps({"tag": tag_name, "data": message_data["content"]}))
                            logger.debug(f"Sent message to WebSocket client {sender_id} from tag {tag_name}")
                except json.JSONDecodeError:
                    logger.error("Could not decode message from Redis channel.")
                except Exception as e:
                    logger.error(f"Error sending message to client {sender_id}: {e}", exc_info=True)

    except asyncio.CancelledError:
        logger.info(f"Redis listener for {sender_id} cancelled.")
    except Exception as e:
        logger.error(f"Critical error in redis_listener for {sender_id}: {e}", exc_info=True)
    finally:
        await pubsub.unsubscribe(*channels)
        logger.info(f"Client {sender_id} unsubscribed from Redis channels.")