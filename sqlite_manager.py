import sqlite3
import os
import json
import logging

logger = logging.getLogger("WebSocketAgent")

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

    db_path = "test_database.db"
    user_table = "user_tokens"

    # Initialize the SQLiteManager
    db_manager = SQLiteManager(db_path, user_table)

    # Test inserting a token and checking it
    test_token = "test_token"
    test_permissions = json.dumps({
        "tag1": {"send": True, "receive": True},
        "tag2": {"send": False, "receive": True}
    })

    # Insert test data into the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO {user_table} (token, permissions) VALUES (?, ?)", (test_token, test_permissions))
    conn.commit()
    conn.close()

    # Now check if we can retrieve the permissions for the test token
    permissions = db_manager.check_token(test_token)
    if permissions:
        logger.info(f"Permissions for token '{test_token}': {permissions}")
    else:
        logger.warning(f"Token '{test_token}' not found in the database.")
