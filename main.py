# main.py (Final, Robust Version)

import asyncio
import websockets
import uuid
import logging
import redis as redis_main 
from handlers.config import load_config
from handlers.sqlite_manager import SQLiteManager
from handlers.redis_client import create_redis_connection
from handlers.connection_manager import manage_client_session
from handlers.commands_listener import commands_listener
from handlers.logger import logger
import click
class Server:
    def __init__(self, config, db_manager=None):
        self.active_connections = {}
        self.config = config
        self.db_manager = db_manager
        self.redis_publisher = None
        self.redis_subscriber = None
        logger.info("Server instance created.")

    async def start(self):
        """Initializes resources and starts the server."""
        try:
            self.redis_publisher = await create_redis_connection(self.config['redis'])
            self.redis_subscriber = await create_redis_connection(self.config['redis'])
        except redis_main.exceptions.ConnectionError:

            logger.critical("Server startup aborted due to Redis connection failure.")
            return 
        
        command_task = asyncio.create_task(
            commands_listener(self.config, self.active_connections, self.redis_subscriber)
        )

        logger.info(f"Starting WebSocket server on ws://{self.config['host']}:{self.config['port']}")
        
        async with websockets.serve(self.handler, self.config['host'], self.config['port']):
            await asyncio.Future()

    async def handler(self, websocket, path):
        connection_id = str(uuid.uuid4())
        try:
            await manage_client_session(
                websocket, self.config, self.db_manager, self.active_connections,
                connection_id, self.redis_publisher, self.redis_subscriber
            )
        except Exception as e:
            logger.error(f"An error occurred in handler for connection {connection_id}: {e}", exc_info=True)
        finally:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
                logger.info(f"Connection {connection_id} removed from active list. Total: {len(self.active_connections)}")

if __name__ == "__main__":
    @click.group(help="WebSocket Server CLI - Manage and run the server")
    def cli():
        click.echo("WebSocket Server CLI")
        pass

    @click.command(help="Start the WebSocket server")
    @click.option("--port", type=int, help="Port to run the server on", default=None)
    def runserver(port):
        config = load_config()
        if port:
            config['port'] = port
        db_manager = None
        if "sql" in config.get("mode", ""):
            db_manager = SQLiteManager(config['database']['path'], config['database']['user_table'])
        if "single_private_key" in config.get("mode", ""):
            pass
        server = Server(config, db_manager)
        try:
            asyncio.run(server.start())
        except KeyboardInterrupt:
            logger.info("Server shut down by user.")

        
    cli.add_command(runserver)
    cli()