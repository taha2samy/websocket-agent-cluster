import configparser
import json
import logging

def load_config(filename="config.conf"):
    config = configparser.ConfigParser()
    config.read(filename)

    # Server settings
    host = config.get("server", "host")
    port = config.getint("server", "port")

    # Load auth tokens and permissions
    if "config" in str(config.get("auth","mode")).lower():
        tokens = json.loads(config.get("auth", "tokens"))
        database=None
    else:
        database={"path":config.get("databses", "path"),"user_table":config.get("databses", "user_table")}
        tokens={}

    # Message type
    message_type = config.get("message", "type")

    # Redis settings
    redis_host = config.get("redis", "host")
    redis_port = config.getint("redis", "port")
    channel_prefix = config.get("redis", "channel")

    logging.info(f"Configuration loaded: host={host}, port={port}, Redis={redis_host}:{redis_port}, message type={message_type}")

    return {
        "host": host,
        "port": port,
        "mode": str(config.get("auth","mode")).lower(),
        "database":database,
        "tokens": tokens,
        "message_type": message_type,
        "server":{"comands_channel":config.get("server","redis_comand_channel"),
                  "comands_metadata":config.get("server","redis_comand_meta")
                  },
        "redis": {
            "host": redis_host,
            "port": redis_port,
            "channel_prefix": channel_prefix,
        },
    }
