import asyncio
import websockets
from config import load_config
from logger import setup_logger
from websocket_handler import process_message
from sqlite_manager import SQLiteManager

async def start_server(config, db_manager=None):
    async with websockets.serve(lambda ws, path: process_message(ws, path, config, db_manager), config['host'], config['port']):
        await asyncio.Future()  # Keep server running

if __name__ == "__main__":
    logger = setup_logger()
    config = load_config()
    db_manager = None
    if "sql" in config["mode"]:
        db_manager = SQLiteManager(config['database']['path'], config['database']['user_table'])

    try:
        asyncio.run(start_server(config, db_manager))
    except KeyboardInterrupt:
        logger.info("Server shut down.")
