import sqlite3
import os
import json
import logging
from handlers.logger import logger

class SQLiteManager:
    def __init__(self, db_path, user_table):
        self.db_path = db_path
        self.user_table = user_table
        self.create_database()

    def create_database(self):
        if not os.path.exists(self.db_path):
            logger.info(f"Creating database at {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.user_table} (
                    id INTEGER PRIMARY KEY,
                    token TEXT UNIQUE,
                    permissions TEXT
                )
            """)
            conn.commit()
            conn.close()

    def check_token(self, token):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT permissions FROM {self.user_table} WHERE token = ?", (token,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])  # Assuming permissions are stored as JSON string
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')