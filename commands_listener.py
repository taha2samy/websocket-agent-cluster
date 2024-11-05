# commands_listener.py
import asyncio
import json
import logging
from redis_client import create_redis_connection

logger = logging.getLogger("WebSocketAgent")

async def commands_listener(config, active_connections):
    client_redis = await create_redis_connection(config['redis'])  # Separate connection for commands_listener
    pubsub = client_redis.pubsub()
    await pubsub.subscribe(config['server']['commands'])

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
