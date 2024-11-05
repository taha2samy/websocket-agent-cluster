# handlers/redis_listener.py
import asyncio
import json
import logging
from redis_client import create_redis_connection

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
