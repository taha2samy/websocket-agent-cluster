import logging

logger = logging.getLogger("WebSocketAgent")
logger.setLevel(logging.INFO)

# Optional: add a StreamHandler if you want console output
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)