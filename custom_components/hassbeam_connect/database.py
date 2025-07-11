"""
Database operations for HassBeam Connect integration.

This module handles all SQLite database operations for storing and retrieving
IR codes captured from HassBeam devices. It provides functions for:

- Database initialization and table creation
- Storing IR codes with device and action metadata
- Retrieving stored codes with optional filtering
- Checking for duplicate entries
- Deleting unwanted codes

The database uses SQLite for local storage and maintains a simple schema
with automatic timestamps for tracking when codes were captured.
"""
import sqlite3
import json
import logging
from typing import Dict, Any, List, Tuple, Optional

_LOGGER = logging.getLogger(__name__)


def init_db(path: str) -> None:
    """
    Initialize the SQLite database with required tables.
    
    Creates the ir_codes table if it doesn't exist. The table structure includes:
    - id: Primary key, auto-incrementing integer
    - device: Device name (sanitized string)
    - action: Action name (sanitized string)
    - event_data: JSON string containing the raw IR data
    - created_at: Timestamp of when the code was stored
    
    Args:
        path (str): File path where the SQLite database should be created/opened
        
    Raises:
        sqlite3.Error: If database initialization fails
    """
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
    """
    Check if an IR code with the same device and action combination already exists.
    
    This function prevents duplicate entries by checking if a code with the same
    device and action combination is already stored in the database.
    
    Args:
        path (str): Path to the SQLite database file
        device (str): Device name (sanitized)
        action (str): Action name (sanitized)
        
    Returns:
        bool: True if a matching code exists, False otherwise
    """
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
    """
    Save an IR code to the database.
    
    Stores the IR code data along with device and action metadata. The function
    automatically checks for duplicates and prevents storing the same device/action
    combination multiple times.
    
    Args:
        path (str): Path to the SQLite database file
        device (str): Device name (sanitized)
        action (str): Action name (sanitized)
        event_data (Dict[str, Any]): Raw IR event data from the device
        
    Returns:
        bool: True if the code was saved successfully, False otherwise
    """
    # Check if an entry with the same device and action already exists
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
    """
    Delete an IR code from the database by ID.
    
    Removes a specific IR code entry from the database using its unique ID.
    
    Args:
        path (str): Path to the SQLite database file
        code_id (int): Unique ID of the IR code to delete
        
    Returns:
        bool: True if the code was deleted successfully, False if not found
    """
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


def get_ir_codes(path: str, device: Optional[str] = None, action: Optional[str] = None, limit: int = 10) -> List[Tuple]:
    """
    Retrieve IR codes from the database with optional filtering.
    
    Fetches IR codes from the database with support for filtering by device and/or action.
    Results are ordered by creation timestamp (newest first) and limited to prevent
    memory issues with large datasets.
    
    Args:
        path (str): Path to the SQLite database file
        device (Optional[str]): Filter by device name (sanitized). If None, all devices included
        action (Optional[str]): Filter by action name (sanitized). If None, all actions included
        limit (int): Maximum number of results to return (default: 10)
        
    Returns:
        List[Tuple]: List of tuples containing (id, device, action, event_data, created_at)
                     Returns empty list if no codes found or on error
    """
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            
            # Build query dynamically based on filter parameters
            if device and action:
                # Filter by both device and action
                cursor.execute(
                    "SELECT * FROM ir_codes WHERE device = ? AND action = ? ORDER BY created_at DESC LIMIT ?",
                    (device, action, limit)
                )
            elif device:
                # Filter by device only
                cursor.execute(
                    "SELECT * FROM ir_codes WHERE device = ? ORDER BY created_at DESC LIMIT ?",
                    (device, limit)
                )
            elif action:
                # Filter by action only
                cursor.execute(
                    "SELECT * FROM ir_codes WHERE action = ? ORDER BY created_at DESC LIMIT ?",
                    (action, limit)
                )
            else:
                # No filters, get all codes
                cursor.execute("SELECT * FROM ir_codes ORDER BY created_at DESC LIMIT ?", (limit,))
                
            results = cursor.fetchall()
            _LOGGER.debug("Retrieved %d IR codes", len(results))
            return results
            
    except sqlite3.Error as err:
        _LOGGER.error("Failed to retrieve IR codes: %s", err)
        return []
