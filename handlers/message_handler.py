# handlers/message_handler.py

import json
import xml.etree.ElementTree as ET
import logging

from handlers.logger import logger

async def handle_message(message, allowed_tags, permissions, sender_id, config, redis_publisher):
    """Parses a client's message and publishes it to the appropriate Redis channels."""
    target_tags = allowed_tags # Default to all allowed tags

    # Determine target tags based on message content and type
    if "json" in config['message_type']:
        try:
            message_data = json.loads(message)
            tags = message_data.get("tags") # Corrected from "tag"
            if tags and isinstance(tags, str):
                target_tags = tags.split(",")
        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message from {sender_id} while in JSON mode. Broadcasting to all allowed tags.")
    
    elif config['message_type'] == "xml":
        try:
            root = ET.fromstring(message)
            tags_element = root.find("tags") # Corrected from "tag"
            if tags_element is not None and tags_element.text:
                target_tags = tags_element.text.split(",")
        except ET.ParseError:
            logger.warning(f"Received malformed XML from {sender_id}. Broadcasting to all allowed tags.")
    
    logger.debug(f"Message from {sender_id} will be published to tags: {target_tags}")

    for tag in target_tags:
        # Check for permission to send on this specific tag
        if tag in allowed_tags and permissions.get(tag, {}).get("send", False):
            redis_channel = f"{config['redis']['channel_prefix']}{tag}"
            payload = json.dumps({"sender_id": sender_id, "content": message})
            await redis_publisher.publish(redis_channel, payload)
            logger.debug(f"Published message from {sender_id} to Redis channel: {redis_channel}")
        else:
            logger.warning(f"Permission denied for sender {sender_id} to send on tag '{tag}'")