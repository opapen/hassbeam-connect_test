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


def check_ir_code_exists(path: str, device: str, action: str) -> bool:
    """Check if an IR code with the same device and action combination already exists."""
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM ir_codes WHERE device = ? AND action = ?",
                (device, action)
            )
            count = cursor.fetchone()[0]
            exists = count > 0
            _LOGGER.debug("IR code exists check for %s.%s: %s", device, action, exists)
            return exists
    except sqlite3.Error as err:
        _LOGGER.error("Failed to check IR code existence: %s", err)
        return False


def save_ir_code(path: str, device: str, action: str, event_data: Dict[str, Any]) -> bool:
    """Save an IR code to the database."""
    # Check if entry already exists
    if check_ir_code_exists(path, device, action):
        error_msg = f"IR code for {device}.{action} already exists"
        _LOGGER.warning(error_msg)
        return False  # Return False instead of raising exception
    
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ir_codes (device, action, event_data) VALUES (?, ?, ?)",
                (device, action, json.dumps(event_data))
            )
            conn.commit()
            _LOGGER.debug("IR code saved: %s.%s", device, action)
            return True
    except sqlite3.Error as err:
        _LOGGER.error("Failed to save IR code: %s", err)
        return False
    except (TypeError, ValueError) as err:
        _LOGGER.error("Invalid data format: %s", err)
        return False


def delete_ir_code(path: str, code_id: int) -> bool:
    """Delete an IR code from the database by ID."""
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ir_codes WHERE id = ?", (code_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                _LOGGER.debug("IR code deleted successfully: ID %d", code_id)
                return True
            else:
                _LOGGER.warning("No IR code found with ID %d", code_id)
                return False
                
    except sqlite3.Error as err:
        _LOGGER.error("Failed to delete IR code: %s", err)
        return False


def get_ir_codes(path: str, device: str = None, action: str = None, limit: int = 10) -> list:
    """Retrieve IR codes from the database."""
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            if device and action:
                cursor.execute(
                    "SELECT * FROM ir_codes WHERE device = ? AND action = ? ORDER BY created_at DESC LIMIT ?",
                    (device, action, limit)
                )
            elif device:
                cursor.execute(
                    "SELECT * FROM ir_codes WHERE device = ? ORDER BY created_at DESC LIMIT ?",
                    (device, limit)
                )
            elif action:
                cursor.execute(
                    "SELECT * FROM ir_codes WHERE action = ? ORDER BY created_at DESC LIMIT ?",
                    (action, limit)
                )
            else:
                cursor.execute("SELECT * FROM ir_codes ORDER BY created_at DESC LIMIT ?", (limit,))
            results = cursor.fetchall()
            _LOGGER.debug("Retrieved %d IR codes", len(results))
            return results
    except sqlite3.Error as err:
        _LOGGER.error("Failed to retrieve IR codes: %s", err)
        return []
