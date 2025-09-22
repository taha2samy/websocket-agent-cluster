# commands_listener.py

import asyncio
import json
import logging
from redis.exceptions import ConnectionError
from handlers.logger import logger


async def commands_listener(config, active_connections, redis_client):
    """Listens on a Redis PubSub channel for server-wide commands."""
    try:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(config['server']['commands_channel'])
        logger.info(f"Subscribed to commands channel: {config['server']['commands_channel']}")
    except ConnectionError as e:
        logger.critical(f"Could not connect to Redis for command listener: {e}")
        return

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0) # Added timeout
            if message and message.get("type") == "message":
                try:
                    command_data = json.loads(message["data"].decode("utf-8"))
                    command = command_data.get("command")
                    target_uuid = command_data.get("uuid")
                    target_token = command_data.get("token")
                    
                    logger.info(f"Received command: {command}")

                    if command == "shutdown":
                        for uuid, conn_info in list(active_connections.items()):
                            await conn_info["websocket"].close(code=4002, reason="Server shutdown command received")
                        logger.info("Shutdown command executed; closing all connections.")
                        break # Exit the loop to allow the server to shut down
                    
                    elif command == "close_connection_by_uuid" and target_uuid:
                        if target_uuid in active_connections:
                            await active_connections[target_uuid]["websocket"].close(code=4003, reason="Remote close command by UUID")
                            logger.info(f"Closed connection by UUID: {target_uuid}")
                        else:
                            logger.warning(f"Close command failed: UUID {target_uuid} not found.")

                    elif command == "close_connection_by_token" and target_token:
                        # Iterate over a copy of the items to allow modification
                        for uuid, conn_info in list(active_connections.items()):
                            if conn_info["token"] == target_token:
                                await conn_info["websocket"].close(code=4004, reason="Remote close command by token")
                                logger.info(f"Closed connection with Token: {target_token}, UUID: {uuid}")

                except json.JSONDecodeError:
                    logger.error("Failed to decode command from Redis message.")
                except Exception as e:
                    logger.error(f"Error processing command: {e}", exc_info=True)

    except asyncio.CancelledError:
        logger.info("Commands listener task cancelled.")
    except Exception as e:
        logger.error(f"Critical error in commands_listener: {e}", exc_info=True)
    finally:
        await pubsub.unsubscribe()
        logger.info("Unsubscribed from commands channel.")