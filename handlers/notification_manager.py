# handlers/notification_manager.py

import json
import logging
from redis.exceptions import ConnectionError

logger = logging.getLogger("WebSocketAgent")

async def publish_notification(notification, config, redis_publisher):
    """Publishes a notification message to the metadata/commands Redis channel."""
    try:
        channel = config['server']['commands_metadata_channel'] # Assuming a clear name in config
        await redis_publisher.publish(channel, json.dumps(notification))
        logger.debug(f"Published notification to {channel}: {notification.get('action')}")
    except ConnectionError as e:
        logger.error(f"Failed to publish notification due to Redis connection error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while publishing notification: {e}", exc_info=True)