"""Database operations for Hassbeam Connect."""
import sqlite3
import json
import logging
from typing import Dict, Any

_LOGGER = logging.getLogger(__name__)


def init_db(path: str) -> None:
    """Initialize the database with required tables."""
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ir_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device TEXT NOT NULL,
                    action TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            _LOGGER.debug("Database initialized successfully: %s", path)
    except sqlite3.Error as err:
        _LOGGER.error("Database initialization failed: %s", err)
        raise


def save_ir_code(path: str, device: str, action: str, event_data: Dict[str, Any]) -> None:
    """Save an IR code to the database."""
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ir_codes (device, action, event_data) VALUES (?, ?, ?)",
                (device, action, json.dumps(event_data))
            )
            conn.commit()
            _LOGGER.debug("IR code saved: %s.%s", device, action)
    except sqlite3.Error as err:
        _LOGGER.error("Failed to save IR code: %s", err)
        raise
    except (TypeError, ValueError) as err:
        _LOGGER.error("Invalid data format: %s", err)
        raise


def get_ir_codes(path: str, device: str = None) -> list:
    """Retrieve IR codes from the database."""
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            if device:
                cursor.execute(
                    "SELECT * FROM ir_codes WHERE device = ? ORDER BY created_at DESC",
                    (device,)
                )
            else:
                cursor.execute("SELECT * FROM ir_codes ORDER BY created_at DESC")
            
            results = cursor.fetchall()
            _LOGGER.debug("Retrieved %d IR codes", len(results))
            return results
    except sqlite3.Error as err:
        _LOGGER.error("Failed to retrieve IR codes: %s", err)
        return []
