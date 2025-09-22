# redis_client.py

"""
Handles all interactions with the Redis server.

This module is responsible for establishing, validating, and managing the asynchronous
connection to Redis, ensuring that the rest of the application has a reliable
client to interact with. It includes a standalone test for quick diagnostics.
"""

import asyncio
import logging
import redis.asyncio as redis
import redis as redis_main  # Imported for access to the library's exception classes

logger = logging.getLogger("WebSocketAgent")


async def create_redis_connection(redis_config: dict) -> redis.Redis:
    """
    Establishes and validates an asynchronous connection to the Redis server.

    This function attempts to connect to Redis using the provided configuration.
    It then performs a PING command as a health check to ensure the connection
    is active and ready for use before returning the client instance.

    Args:
        redis_config (dict): A dictionary containing 'host' and 'port' for Redis.

    Returns:
        redis.Redis: An active and validated Redis client instance.

    Raises:
        redis.exceptions.ConnectionError: If the connection to the Redis server
            cannot be established (e.g., server is down, wrong address).
        asyncio.TimeoutError: If the connection attempt times out.
    """
    redis_url = f"redis://{redis_config['host']}:{redis_config['port']}"
    logger.info(f"Attempting to connect to Redis at {redis_url}...")
    
    try:
        # Initialize the client from the URL.
        # `decode_responses=True` is a best practice to ensure Redis commands
        # return Python strings instead of bytes, simplifying the rest of the code.
        client = redis.from_url(redis_url, decode_responses=True)

        # Perform a PING command as a mandatory health check to validate the connection.
        # This prevents the application from starting with a faulty Redis link.
        await client.ping()
        
        logger.info("Successfully connected and validated Redis server connection.")
        return client
    
    except redis_main.exceptions.ConnectionError as e:
        # Catching specific connection errors provides clear, actionable log messages.
        logger.critical(f"FATAL: Could not connect to Redis at {redis_url}. Verify the server is running and accessible.")
        logger.critical(f"Underlying error: {e}")
        # Re-raise the exception to ensure the main application startup is aborted,
        # as a Redis connection is critical for its operation.
        raise 
    
    except asyncio.TimeoutError:
        logger.critical(f"FATAL: Connection to Redis at {redis_url} timed out.")
        raise
    
    except Exception as e:
        # A general catch-all for any other unexpected issues during initialization.
        logger.critical(f"An unexpected error occurred while connecting to Redis: {e}")
        raise


if __name__ == "__main__":
    """
    Provides a standalone execution block to test the Redis connection functionality
    independently from the main WebSocket server.
    """
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    # A sample configuration for direct testing.
    # Adjust if your local Redis instance uses a different host or port.
    test_redis_config = {
        "host": "localhost",
        "port": 6379
    }

    async def run_test():
        print("-" * 50)
        print("Running standalone Redis connection test...")
        print("-" * 50)
        redis_client = None
        try:
            redis_client = await create_redis_connection(test_redis_config)
            if redis_client:
                print("\nSUCCESS: Redis connection test passed.")
                # Perform a quick SET/GET/DELETE to confirm operational status.
                await redis_client.set("health_check_key", "123")
                value = await redis_client.get("health_check_key")
                print(f"Verified SET/GET operation: 'health_check_key' has value '{value}'")
                await redis_client.delete("health_check_key")
        except Exception:
            # The create_redis_connection function already provides detailed critical logs.
            print(f"\nFAILED: Redis connection test failed. Check logs above for details.")
        finally:
            if redis_client:
                # Always ensure the test connection is closed properly.
                await redis_client.close()
                logger.info("Test connection to Redis closed.")
        print("-" * 50)

    asyncio.run(run_test())