# handlers/notification_manager.py
import json
from redis_client import create_redis_connection

async def publish_notification(notification, config):
    client_redis = await create_redis_connection(config['redis'])
    channel = f"{config['server']['comands_metadata']}"
    await client_redis.publish(channel, json.dumps(notification))
    await client_redis.close()
