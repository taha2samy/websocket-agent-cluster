import asyncio
import configparser
import json
import websockets
import aioredis
import logging
import uuid
import xml.etree.ElementTree as ET  # مكتبة لتحليل XML

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("WebSocketAgent")

# Load configuration from .conf file
logger.info("Loading configurations")
config = configparser.ConfigParser()
config.read("config.conf")

# Server settings from .conf file
HOST = config.get("server", "host")
PORT = config.getint("server", "port")

# Load auth tokens and permissions
TOKENS = json.loads(config.get("auth", "tokens"))

# Message type
MESSAGE_TYPE = config.get("message", "type")

# Redis settings from .conf file
REDIS_HOST = config.get("redis", "host")
REDIS_PORT = config.getint("redis", "port")
CHANNEL_PREFIX = config.get("redis", "channel")
logger.info(f"Configuration loaded: host={HOST}, port={PORT}, Redis={REDIS_HOST}:{REDIS_PORT}")
logger.info(f"message type {MESSAGE_TYPE}")
async def create_redis_connection():
    return aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")

async def process_message(websocket, path):
    headers = websocket.request_headers
    token = headers.get("Authorization")

    # Validate token and retrieve permissions
    if token not in TOKENS:
        await websocket.close(code=4001, reason="Unauthorized")
        logger.warning("Unauthorized access attempt.")
        return

    token_data = TOKENS[token]
    allowed_tags = token_data["tags"]
    permissions = token_data["permissions"]

    logger.info(f"Client connected with token: {token} and allowed tags: {allowed_tags}")

    # Unique identifier for each client to avoid self-receiving messages
    sender_id = str(uuid.uuid4())

    # Create a dedicated Redis pub/sub instance for this client
    client_redis = await create_redis_connection()
    pubsub = client_redis.pubsub()

    # Prepare channels for subscription based on the client's receive permissions
    receive_channels = [f"{CHANNEL_PREFIX}{tag}" for tag in allowed_tags if permissions.get(tag, {}).get("receive")]

    # Subscribe to channels for reading
    await pubsub.subscribe(*receive_channels)

    async def redis_listener():
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    message_data = json.loads(message["data"].decode("utf-8"))
                    if message_data.get("sender_id") != sender_id:
                        tag_name = message["channel"].decode("utf-8").replace(CHANNEL_PREFIX, "")
                        if permissions.get(tag_name, {}).get("receive"):
                            await websocket.send(json.dumps({"tag": tag_name, "data": message_data["content"]}))
                            logger.debug(f"Message sent to WebSocket client on tag {tag_name}: {message_data['content']}")
                await asyncio.sleep(0.1)  # Add a small delay to prevent busy-waiting
        except Exception as e:
            logger.error(f"Error in redis_listener: {e}")
        finally:
            await pubsub.unsubscribe(*receive_channels)  # Unsubscribe on disconnect

    listener_task = asyncio.create_task(redis_listener())

    try:
        async for message in websocket:
            logger.info(f"=-sss{allowed_tags}")
            if  "json" in MESSAGE_TYPE:
                try:
                    message_data = json.loads(message)
                    tags = message_data.get("tags")
                    if tags:
                        target_tags = tags.split(",")  
                        
                    else:
                        target_tags = allowed_tags
                except:
                    target_tags = allowed_tags
                    logger.error("Invalid JSON message format")

            elif MESSAGE_TYPE == "xml":
                try:
                    root = ET.fromstring(message)
                    tags_element = root.find("tags")
                    if tags_element is not None:
                        target_tags = tags_element.text.split(",")  # تحويل tags إلى قائمة
                    else:
                        target_tags = allowed_tags
                except:
                    target_tags = allowed_tags
                    logger.error("Invalid XML message format")
                    continue

            else:
                target_tags = allowed_tags
            logger.error(f"wwwwv  {target_tags}")
            for tag in target_tags:
                if tag in allowed_tags and permissions.get(tag, {}).get("send"):
                    redis_channel = f"{CHANNEL_PREFIX}{tag}"
                    payload = json.dumps({"sender_id": sender_id, "content": message})
                    await client_redis.publish(redis_channel, payload)
                    logger.debug(f"Published message to Redis channel {redis_channel}: {message}")
                else:
                    logger.warning(f"Send permission denied for tag {tag}")
    except websockets.ConnectionClosedError:
        logger.info("Connection closed by client")
    finally:
        listener_task.cancel()
        await client_redis.close()
        logger.info("Client Redis connection closed")

# Start the WebSocket server
async def start_server():
    logger.info(f"Starting server on ws://{HOST}:{PORT}")
    async with websockets.serve(process_message, HOST, PORT):
        await asyncio.Future()  # Keep server running

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server shut down.")
