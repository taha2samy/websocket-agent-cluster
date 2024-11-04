import aioredis
import logging

logger = logging.getLogger("WebSocketAgent")

async def create_redis_connection(redis_config):
    redis_url = f"redis://{redis_config['host']}:{redis_config['port']}"
    logger.info(f"Connecting to Redis at {redis_url}")
    return await aioredis.from_url(redis_url)
