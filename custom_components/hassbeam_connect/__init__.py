"""
HassBeam Connect Integration for Home Assistant

This custom integration provides a bridge between HassBeam IR devices and Home Assistant,
allowing users to capture, store, and manage IR codes from their remote controls.

Services provided:
- get_recent_codes: Retrieve captured IR codes with optional filtering
- save_ir_code: Store IR codes with device and action names
- delete_ir_code: Remove codes from the database
"""

import json
import logging
import re
import unicodedata
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, DB_NAME
from .database import init_db, get_ir_codes, save_ir_code, check_ir_code_exists, delete_ir_code

_LOGGER = logging.getLogger(__name__)


def sanitize_string(value: str) -> str:
    """
    Sanitize device and action strings for consistent database storage.
    
    Converts input to lowercase, replaces special characters, and normalizes
    the string for database storage.
    """
    if not value:
        return ""
    
    # Convert to lowercase
    value = value.lower()
    
    # Replace common special characters
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'å': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u',
        'ñ': 'n', 'ç': 'c'
    }
    
    for original, replacement in replacements.items():
        value = value.replace(original, replacement)
    
    # Normalize Unicode and remove accents
    value = unicodedata.normalize('NFD', value)
    value = ''.join(c for c in value if unicodedata.category(c) != 'Mn')
    
    # Clean up formatting
    value = re.sub(r'[\s\-]+', '_', value)  # Replace spaces/hyphens with underscores
    value = re.sub(r'[^a-z0-9_]', '', value)  # Remove non-alphanumeric chars
    value = re.sub(r'_+', '_', value)  # Replace multiple underscores with single
    value = value.strip('_')  # Remove leading/trailing underscores
    
    return value if value else "unknown"


def _format_codes(codes):
    """Format codes for API response."""
    return [
        {
            "id": code[0],
            "device": code[1],
            "action": code[2],
            "event_data": code[3],
            "created_at": code[4],
        }
        for code in codes
    ]


def _parse_event_data(event_data):
    """Parse event data from string or return as-is."""
    if isinstance(event_data, str):
        try:
            return json.loads(event_data)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in event_data")
    return event_data


def _fire_event(hass, event_name, data):
    """Fire an event with logging."""
    _LOGGER.info("Firing event: %s with data: %s", event_name, data)
    hass.bus.fire(event_name, data)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HassBeam Connect from a config entry."""
    _LOGGER.debug("Setting up HassBeam Connect integration")

    # Initialize integration data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = entry.data

    # Initialize database
    try:
        db_path = hass.config.path(DB_NAME)
        init_db(db_path)
        _LOGGER.info("Database initialized successfully: %s", db_path)
    except Exception as err:
        _LOGGER.error("Failed to initialize database: %s", err)
        return False

    # Register service handlers
    _register_services(hass)

    _LOGGER.info("HassBeam Connect integration setup completed successfully")
    return True


def _register_services(hass: HomeAssistant):
    """Register all service handlers."""
    
    async def handle_get_recent_codes(call):
        """Handle get_recent_codes service."""
        _LOGGER.info("Service 'get_recent_codes' called with data: %s", call.data)
        
        # Extract and sanitize parameters
        device_raw = call.data.get("device")
        action_raw = call.data.get("action")
        limit = call.data.get("limit", 10)
        
        device = sanitize_string(device_raw) if device_raw else None
        action = sanitize_string(action_raw) if action_raw else None
        
        if device_raw or action_raw:
            _LOGGER.info("Sanitized search - Original: '%s.%s' -> Sanitized: '%s.%s'", 
                        device_raw or "None", action_raw or "None", 
                        device or "None", action or "None")

        try:
            db_path = hass.config.path(DB_NAME)
            codes = get_ir_codes(db_path, device, action, limit)
            formatted_codes = _format_codes(codes)

            _LOGGER.info("Retrieved %d codes", len(formatted_codes))
            _fire_event(hass, f"{DOMAIN}_codes_retrieved", {"codes": formatted_codes})
            
            return {"codes": formatted_codes}

        except Exception as err:
            _LOGGER.error("Failed to retrieve IR codes: %s", err)
            return {"codes": []}

    async def handle_save_ir_code(call):
        """Handle save_ir_code service."""
        _LOGGER.info("Service 'save_ir_code' called with data: %s", call.data)
        
        # Extract parameters
        device_raw = call.data.get("device", "").strip()
        action_raw = call.data.get("action", "").strip()
        event_data = call.data.get("event_data", "")

        # Validate required parameters
        if not device_raw:
            _LOGGER.error("Device is required")
            return {"success": False, "error": "Device is required"}
        
        if not action_raw:
            _LOGGER.error("Action is required")
            return {"success": False, "error": "Action is required"}
        
        if not event_data:
            _LOGGER.error("Event data is required")
            return {"success": False, "error": "Event data is required"}

        # Sanitize parameters
        device = sanitize_string(device_raw)
        action = sanitize_string(action_raw)
        
        _LOGGER.info("Sanitized values - Original: '%s.%s' -> Sanitized: '%s.%s'", 
                    device_raw, action_raw, device, action)

        try:
            # Parse event data
            event_data = _parse_event_data(event_data)
            
            # Check for duplicates
            db_path = hass.config.path(DB_NAME)
            if check_ir_code_exists(db_path, device, action):
                error_msg = f"IR code for {device_raw}.{action_raw} already exists"
                _LOGGER.error(error_msg)
                
                _fire_event(hass, f"{DOMAIN}_code_saved", {
                    "device": device_raw,
                    "action": action_raw,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}

            # Save to database
            success = save_ir_code(db_path, device, action, event_data)
            
            if success:
                _LOGGER.info("IR code saved successfully for %s.%s", device_raw, action_raw)
                
                _fire_event(hass, f"{DOMAIN}_code_saved", {
                    "device": device_raw,
                    "action": action_raw,
                    "success": True
                })
                
                return {"success": True, "device": device_raw, "action": action_raw}
            else:
                error_msg = f"Failed to save IR code for {device_raw}.{action_raw}"
                _LOGGER.error(error_msg)
                
                _fire_event(hass, f"{DOMAIN}_code_saved", {
                    "device": device_raw,
                    "action": action_raw,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}

        except ValueError as err:
            _LOGGER.error("Invalid event data: %s", err)
            return {"success": False, "error": str(err)}
        except Exception as err:
            _LOGGER.error("Failed to save IR code: %s", err)
            
            _fire_event(hass, f"{DOMAIN}_code_saved", {
                "device": device_raw,
                "action": action_raw,
                "success": False,
                "error": str(err)
            })
            
            return {"success": False, "error": str(err)}

    async def handle_delete_ir_code(call):
        """Handle delete_ir_code service."""
        _LOGGER.info("Service 'delete_ir_code' called with data: %s", call.data)
        
        code_id = call.data.get("id")
        
        if not code_id:
            _LOGGER.error("ID is required")
            return {"success": False, "error": "ID is required"}

        # Validate ID
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
                
                _fire_event(hass, f"{DOMAIN}_code_deleted", {
                    "id": code_id,
                    "success": True
                })
                
                return {"success": True, "id": code_id}
            else:
                error_msg = f"No IR code found with ID {code_id}"
                _LOGGER.warning(error_msg)
                
                _fire_event(hass, f"{DOMAIN}_code_deleted", {
                    "id": code_id,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}

        except Exception as err:
            _LOGGER.error("Failed to delete IR code: %s", err)
            
            _fire_event(hass, f"{DOMAIN}_code_deleted", {
                "id": code_id,
                "success": False,
                "error": str(err)
            })
            
            return {"success": False, "error": str(err)}

    # Register all services
    hass.services.async_register(DOMAIN, "get_recent_codes", handle_get_recent_codes)
    hass.services.async_register(DOMAIN, "save_ir_code", handle_save_ir_code)
    hass.services.async_register(DOMAIN, "delete_ir_code", handle_delete_ir_code)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up resources."""
    _LOGGER.debug("Unloading HassBeam Connect integration")

    # Remove all registered services
    services = ["get_recent_codes", "save_ir_code", "delete_ir_code"]
    for service in services:
        hass.services.async_remove(DOMAIN, service)

    # Clear stored data
    hass.data.pop(DOMAIN, None)

    _LOGGER.info("HassBeam Connect integration unloaded successfully")
    return True


