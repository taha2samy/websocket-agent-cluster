import json
import sqlite3
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from handlers.logger import logger

def open_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    return conn, cursor

def insert_or_update_token(cursor, user_table, token, permissions):
    permissions_json = json.dumps(permissions, sort_keys=True)
    cursor.execute(f"SELECT permissions FROM {user_table} WHERE token = ?", (token,))
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            f"INSERT INTO {user_table} (token, permissions) VALUES (?, ?)",
            (token, permissions_json)
        )
        logger.debug(f"Inserted token: {token}")
    else:
        existing_permissions_json = row[0]
        if existing_permissions_json != permissions_json:
            cursor.execute(
                f"UPDATE {user_table} SET permissions = ? WHERE token = ?",
                (permissions_json, token)
            )
            logger.debug(f"Updated permissions for token: {token}")
        else:
            logger.warning(f"Token {token} already exists with same permissions")

def process_json_file(db_path, user_table, json_file):
    with open(json_file, "r") as f:
        logger.debug(f"Loading permissions from {json_file}")
        data = json.load(f)
        

    if "tests_data" not in data:
        raise ValueError("JSON file must contain 'tests_data' key")

    data_list = data["tests_data"]

    conn, cursor = open_db(db_path)

    for entry in data_list:
        token = entry["token"]
        permissions = entry["permissions"]
        insert_or_update_token(cursor, user_table, token, permissions)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    db_path = "database.db"
    user_table = "user_tokens"
    json_file = "scripts/permissions/permisssions.json"

    process_json_file(db_path, user_table, json_file)
