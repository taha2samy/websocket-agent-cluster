# handlers/message_handler.py
import json
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger("WebSocketAgent")

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
