import sqlite3
import json

def init_db(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ir_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT NOT NULL,
            action TEXT NOT NULL,
            event_data TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_ir_code(path, device, action, event_data):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO ir_codes (device, action, event_data) VALUES (?, ?, ?)",
        (device, action, json.dumps(event_data))
    )
    conn.commit()
    conn.close()
