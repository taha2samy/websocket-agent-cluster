# websocket_handler.py
import asyncio
import logging
import websockets
from handlers.connection_manager import process_message
from commands_listener import commands_listener
from config import load_config
logger = logging.getLogger("WebSocketAgent")

async def main(config):
    async with websockets.serve(lambda ws, path: process_message(ws, path, config), config['server']['host'], config['server']['port']):
        logger.info("WebSocket server started...")
        await commands_listener(config, active_connections)

if __name__ == "__main__":
    config = load_config()  # Function to load configuration
    active_connections = {}  # Maintain active connections
    asyncio.run(main(config))
