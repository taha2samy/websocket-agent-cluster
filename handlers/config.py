# config.py (Corrected and Final Version)

import configparser
import json
import logging
from handlers.logger import logger

def load_config(filename="config.conf"):
    config = configparser.ConfigParser()
    config.read(filename)

    # Server settings
    host = config.get("server", "host")
    port = config.getint("server", "port")
    
    auth_mode = str(config.get("auth", "mode")).lower()
    tokens = {}
    database = None

    # Load auth tokens and permissions based on the mode
    if "config" in auth_mode:
        # Load tokens directly from the config file's JSON string
        tokens_str = config.get("auth", "tokens", fallback="{}")
        tokens = json.loads(tokens_str)
    elif "sql" in auth_mode:
        # Get database configuration details for SQLiteManager
        database = {
            "path": config.get("databases", "path"),
            "user_table": config.get("databases", "user_table")
        }
    
    # Message type
    message_type = config.get("message", "type")

    # Redis settings
    redis_host = config.get("redis", "host")
    redis_port = config.getint("redis", "port")
    channel_prefix = config.get("redis", "channel_prefix") 

    logging.info(f"Configuration loaded: host={host}, port={port}, AuthMode={auth_mode}, Redis={redis_host}:{redis_port}")

    return {
        "host": host,
        "port": port,
        "mode": auth_mode,
        "database": database,
        "tokens": tokens,
        "message_type": message_type,
        "server": {
            # CORRECTED: Spelling and using better names
            "commands_channel": config.get("server", "redis_command_channel"),
            "commands_metadata_channel": config.get("server", "redis_metadata_channel")
        },
        "redis": {
            "host": redis_host,
            "port": redis_port,
            "channel_prefix": channel_prefix,
        },
    }