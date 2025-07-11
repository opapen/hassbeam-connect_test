"""
HassBeam Connect Integration for Home Assistant

This custom integration provides a bridge between HassBeam IR devices and Home Assistant,
allowing users to capture, store, and manage IR codes from their remote controls.

Key Features:
- Capture IR codes from HassBeam devices
- Store codes in local SQLite database
- Retrieve and filter stored codes
- Delete unwanted codes
- Real-time event notifications for frontend cards

Services provided:
- get_recent_codes: Retrieve captured IR codes with optional filtering
- save_ir_code: Store IR codes with device and action names
- delete_ir_code: Remove codes from the database
"""

import logging
import re
import unicodedata
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, DB_NAME
from .database import init_db, get_ir_codes, save_ir_code, check_ir_code_exists, delete_ir_code

_LOGGER = logging.getLogger(__name__)


def sanitize_string(value: str) -> str:
    """
    Sanitize device and action strings for consistent database storage.
    
    This function normalizes user input to ensure consistent storage and retrieval
    of IR codes in the database. It handles various character encodings and
    special characters that might be entered by users.
    
    Process:
    1. Convert to lowercase for case-insensitive matching
    2. Replace common accented characters with ASCII equivalents
    3. Normalize Unicode characters to remove remaining accents
    4. Replace spaces and hyphens with underscores
    5. Remove all non-alphanumeric characters except underscores
    6. Clean up multiple consecutive underscores
    7. Remove leading/trailing underscores
    8. Ensure minimum length requirement
    
    Args:
        value (str): The raw string to be sanitized
        
    Returns:
        str: The sanitized string safe for database storage
        
    Examples:
        >>> sanitize_string("My TV Remote")
        'my_tv_remote'
        >>> sanitize_string("Fernbedienung Küche")
        'fernbedienung_kueche'
        >>> sanitize_string("Living Room A/V")
        'living_room_a_v'
    """
    if not value:
        return ""
    
    # Convert to lowercase for consistent comparison
    value = value.lower()
    
    # Replace common accented characters with ASCII equivalents
    # This covers most European languages and common special characters
    character_replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'å': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u',
        'ñ': 'n', 'ç': 'c'
    }
    
    for original_char, replacement_char in character_replacements.items():
        value = value.replace(original_char, replacement_char)
    
    # Normalize Unicode characters to remove any remaining accents
    # NFD = Canonical Decomposition, separates characters from their accents
    value = unicodedata.normalize('NFD', value)
    # Remove all combining characters (accents, diacritics, etc.)
    value = ''.join(c for c in value if unicodedata.category(c) != 'Mn')
    
    # Replace spaces and hyphens with underscores for consistent formatting
    value = re.sub(r'[\s\-]+', '_', value)
    
    # Remove all characters that are not alphanumeric or underscores
    value = re.sub(r'[^a-z0-9_]', '', value)
    
    # Replace multiple consecutive underscores with a single underscore
    value = re.sub(r'_+', '_', value)
    
    # Remove leading and trailing underscores
    value = value.strip('_')
    
    # Ensure the result has at least one character
    if len(value) < 1:
        value = "unknown"
    
    return value


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up HassBeam Connect from a config entry.
    
    This function initializes the integration by:
    1. Storing configuration data in Home Assistant's data registry
    2. Initializing the SQLite database for IR code storage
    3. Registering all service handlers for IR code management
    
    Args:
        hass (HomeAssistant): The Home Assistant instance
        entry (ConfigEntry): The configuration entry for this integration
        
    Returns:
        bool: True if setup was successful, False otherwise
    """
    _LOGGER.debug("Setting up HassBeam Connect integration")

    # Initialize integration data storage
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = entry.data

    # Initialize SQLite database for IR code storage
    try:
        db_path = hass.config.path(DB_NAME)
        init_db(db_path)
        _LOGGER.info("Database initialized successfully: %s", db_path)
    except Exception as err:
        _LOGGER.error("Failed to initialize database: %s", err)
        return False

    async def handle_get_recent_codes_service(call):
        """
        Handle the get_recent_codes service call.
        
        Retrieves IR codes from the database with optional filtering by device and action.
        Supports pagination through the limit parameter.
        
        Service Parameters:
        - device (optional): Filter results by device name
        - action (optional): Filter results by action name  
        - limit (optional): Maximum number of results to return (default: 10)
        
        Returns:
        - Fires 'hassbeam_connect_codes_retrieved' event with retrieved codes
        - Event data contains formatted list of IR codes with metadata
        """
        _LOGGER.info("Service 'get_recent_codes' called with data: %s", call.data)
        device_raw = call.data.get("device")
        action_raw = call.data.get("action")  
        limit = call.data.get("limit", 10)
        # Allow filtering by both device and action parameters

        # Sanitize device and action for database lookup if provided
        device = sanitize_string(device_raw) if device_raw else None
        action = sanitize_string(action_raw) if action_raw else None
        
        if device_raw or action_raw:
            _LOGGER.info("Sanitized search values - Original: '%s.%s' -> Sanitized: '%s.%s'", 
                        device_raw or "None", action_raw or "None", device or "None", action or "None")

        try:
            db_path = hass.config.path(DB_NAME)
            codes = get_ir_codes(db_path, device, action, limit)

            # Format codes for consistent API response
            formatted_codes = [
                {
                    "id": code[0],
                    "device": code[1],
                    "action": code[2],
                    "event_data": code[3],
                    "created_at": code[4],
                }
                for code in codes
            ]

            _LOGGER.info("Event '%s_codes_retrieved' fired with %d codes", DOMAIN, len(formatted_codes))
            # Fire event for listeners (frontend cards)
            hass.bus.fire(f"{DOMAIN}_codes_retrieved", {"codes": formatted_codes})

            return {"codes": formatted_codes}

        except Exception as err:
            _LOGGER.error("Failed to retrieve IR codes: %s", err)
            return {"codes": []}

    async def handle_save_ir_code_service(call):
        """
        Handle the save_ir_code service call.
        
        Saves IR code data to the database with proper validation and duplicate checking.
        
        Service Parameters:
        - device (required): Name of the device (will be sanitized for storage)
        - action (required): Name of the action (will be sanitized for storage)
        - event_data (required): IR event data (JSON string or object)
        
        Returns:
        - Fires 'hassbeam_connect_code_saved' event with operation result
        - Event contains success status and error message if applicable
        """
        _LOGGER.info("Service 'save_ir_code' called with data: %s", call.data)
        device_raw = call.data.get("device", "").strip()
        action_raw = call.data.get("action", "").strip()
        event_data = call.data.get("event_data", "")

        # Validate required parameters
        if not device_raw:
            _LOGGER.error("Device is required for save_ir_code service")
            return {"success": False, "error": "Device is required"}

        if not action_raw:
            _LOGGER.error("Action is required for save_ir_code service")
            return {"success": False, "error": "Action is required"}

        # Sanitize device and action for consistent database storage
        device = sanitize_string(device_raw)
        action = sanitize_string(action_raw)
        
        _LOGGER.info("Sanitized values - Original: '%s.%s' -> Sanitized: '%s.%s'", 
                    device_raw, action_raw, device, action)

        if not event_data:
            _LOGGER.error("Event data is required for save_ir_code service")
            return {"success": False, "error": "Event data is required"}

        try:
            # Parse event_data if it's provided as a JSON string
            if isinstance(event_data, str):
                import json
                try:
                    event_data = json.loads(event_data)
                except json.JSONDecodeError:
                    _LOGGER.error("Invalid JSON in event_data: %s", event_data)
                    return {"success": False, "error": "Invalid JSON in event_data"}
                    
            # Check if an entry with the same device and action already exists
            db_path = hass.config.path(DB_NAME)
            if check_ir_code_exists(db_path, device, action):
                error_msg = f"IR code for {device_raw}.{action_raw} (sanitized: {device}.{action}) already exists"
                _LOGGER.error(error_msg)
                
                # Fire error event for frontend notification
                event_data_event = {
                    "device": device_raw,  # Use original values for frontend display
                    "action": action_raw,
                    "success": False,
                    "error": error_msg
                }
                _LOGGER.info("Firing error event: %s with data: %s", f"{DOMAIN}_code_saved", event_data_event)
                hass.bus.fire(f"{DOMAIN}_code_saved", event_data_event)
                
                return {"success": False, "error": error_msg}

            # Save to database using sanitized values for consistency
            success = save_ir_code(db_path, device, action, event_data)
            
            if success:
                _LOGGER.info("IR code saved successfully for %s.%s (sanitized: %s.%s)", 
                            device_raw, action_raw, device, action)

                # Fire success event using original values for frontend display
                event_data_event = {
                    "device": device_raw, 
                    "action": action_raw,
                    "success": True
                }
                _LOGGER.info("Firing success event: %s with data: %s", f"{DOMAIN}_code_saved", event_data_event)
                hass.bus.fire(f"{DOMAIN}_code_saved", event_data_event)

                return {"success": True, "device": device_raw, "action": action_raw}
            else:
                error_msg = f"Failed to save IR code for {device_raw}.{action_raw} (sanitized: {device}.{action})"
                _LOGGER.error(error_msg)
                
                # Fire error event for frontend notification
                hass.bus.fire(f"{DOMAIN}_code_saved", {
                    "device": device_raw, 
                    "action": action_raw,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}

        except Exception as err:
            _LOGGER.error("Failed to save IR code: %s", err)
            
            # Fire error event using original values for frontend display
            hass.bus.fire(f"{DOMAIN}_code_saved", {
                "device": device_raw, 
                "action": action_raw,
                "success": False,
                "error": str(err)
            })
            
            return {"success": False, "error": str(err)}

    async def handle_delete_ir_code_service(call):
        """
        Handle the delete_ir_code service call.
        
        Deletes a specific IR code from the database using its unique ID.
        
        Service Parameters:
        - id (required): The unique ID of the IR code to delete
        
        Returns:
        - Fires 'hassbeam_connect_code_deleted' event with operation result
        - Event contains success status and error message if applicable
        """
        _LOGGER.info("Service 'delete_ir_code' called with data: %s", call.data)
        code_id = call.data.get("id")

        if not code_id:
            _LOGGER.error("ID is required for delete_ir_code service")
            return {"success": False, "error": "ID is required"}

        # Validate and convert ID to integer
        try:
            code_id = int(code_id)
        except (ValueError, TypeError):
            _LOGGER.error("Invalid ID format: %s", code_id)
            return {"success": False, "error": "Invalid ID format"}

        try:
            db_path = hass.config.path(DB_NAME)
            success = delete_ir_code(db_path, code_id)

            if success:
                _LOGGER.info("IR code deleted successfully: ID %d", code_id)
                
                # Fire success event for frontend notification
                hass.bus.fire(f"{DOMAIN}_code_deleted", {
                    "id": code_id,
                    "success": True
                })
                
                return {"success": True, "id": code_id}
            else:
                error_msg = f"No IR code found with ID {code_id}"
                _LOGGER.warning(error_msg)
                
                # Fire error event for frontend notification
                hass.bus.fire(f"{DOMAIN}_code_deleted", {
                    "id": code_id,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}

        except Exception as err:
            _LOGGER.error("Failed to delete IR code: %s", err)
            
            # Fire error event for frontend notification
            hass.bus.fire(f"{DOMAIN}_code_deleted", {
                "id": code_id,
                "success": False,
                "error": str(err)
            })
            
            return {"success": False, "error": str(err)}

    # Register all service handlers with Home Assistant
    hass.services.async_register(
        DOMAIN, "get_recent_codes", handle_get_recent_codes_service
    )
    
    hass.services.async_register(
        DOMAIN, "save_ir_code", handle_save_ir_code_service
    )
    
    hass.services.async_register(
        DOMAIN, "delete_ir_code", handle_delete_ir_code_service
    )

    _LOGGER.info("HassBeam Connect integration setup completed successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry and clean up resources.
    
    This function removes all registered services and clears stored data
    when the integration is being unloaded or reloaded.
    
    Args:
        hass (HomeAssistant): The Home Assistant instance
        entry (ConfigEntry): The configuration entry being unloaded
        
    Returns:
        bool: True if unload was successful
    """
    _LOGGER.debug("Unloading HassBeam Connect integration")

    # Remove all registered services
    hass.services.async_remove(DOMAIN, "get_recent_codes")
    hass.services.async_remove(DOMAIN, "save_ir_code")
    hass.services.async_remove(DOMAIN, "delete_ir_code")

    # Clear stored data from Home Assistant's data registry
    hass.data.pop(DOMAIN, None)

    _LOGGER.info("HassBeam Connect integration unloaded successfully")
    return True


