"""Hassbeam Connect integration for Home Assistant."""

import logging
import re
import unicodedata
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, DB_NAME
from .database import init_db, get_ir_codes, save_ir_code, check_ir_code_exists, delete_ir_code

_LOGGER = logging.getLogger(__name__)


def sanitize_string(value: str) -> str:
    """Sanitize device and action strings for database storage.
    
    - Convert to lowercase
    - Replace umlauts and special characters
    - Remove/replace special characters and spaces
    - Keep only alphanumeric characters and underscores
    """
    if not value:
        return ""
    
    # Convert to lowercase
    value = value.lower()
    
    # Replace common umlauts and special characters
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'å': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u',
        'ñ': 'n', 'ç': 'c'
    }
    
    for old, new in replacements.items():
        value = value.replace(old, new)
    
    # Normalize unicode characters (remove accents from remaining characters)
    value = unicodedata.normalize('NFD', value)
    value = ''.join(c for c in value if unicodedata.category(c) != 'Mn')
    
    # Replace spaces and hyphens with underscores
    value = re.sub(r'[\s\-]+', '_', value)
    
    # Remove all non-alphanumeric characters except underscores
    value = re.sub(r'[^a-z0-9_]', '', value)
    
    # Remove multiple consecutive underscores
    value = re.sub(r'_+', '_', value)
    
    # Remove leading/trailing underscores
    value = value.strip('_')
    
    # Ensure minimum length
    if len(value) < 1:
        value = "unknown"
    
    return value


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hassbeam Connect from a config entry."""
    _LOGGER.debug("Setting up Hassbeam Connect integration")

    # Store config data
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

    async def handle_get_recent_codes_service(call):
        """Handle the get_recent_codes service call."""
        _LOGGER.info("Service 'get_recent_codes' called with data: %s", call.data)
        device_raw = call.data.get("device")
        action_raw = call.data.get("action")  
        limit = call.data.get("limit", 10)
       # NEW: allow action filter

        # Sanitize device and action for database lookup if provided
        device = sanitize_string(device_raw) if device_raw else None
        action = sanitize_string(action_raw) if action_raw else None
        
        if device_raw or action_raw:
            _LOGGER.info("Sanitized search values - Original: '%s.%s' -> Sanitized: '%s.%s'", 
                        device_raw or "None", action_raw or "None", device or "None", action or "None")

        try:
            db_path = hass.config.path(DB_NAME)
            codes = get_ir_codes(db_path, device, action, limit)  # pass action

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
            # Event für Listener (Cards)
            hass.bus.fire(f"{DOMAIN}_codes_retrieved", {"codes": formatted_codes})

            return {"codes": formatted_codes}

        except Exception as err:
            _LOGGER.error("Failed to retrieve IR codes: %s", err)
            return {"codes": []}

    async def handle_save_ir_code_service(call):
        """Handle the save_ir_code service call."""
        _LOGGER.info("Service 'save_ir_code' called with data: %s", call.data)
        device_raw = call.data.get("device", "").strip()
        action_raw = call.data.get("action", "").strip()
        event_data = call.data.get("event_data", "")

        if not device_raw:
            _LOGGER.error("Device is required for save_ir_code service")
            return {"success": False, "error": "Device is required"}

        if not action_raw:
            _LOGGER.error("Action is required for save_ir_code service")
            return {"success": False, "error": "Action is required"}

        # Sanitize device and action for database storage
        device = sanitize_string(device_raw)
        action = sanitize_string(action_raw)
        
        _LOGGER.info("Sanitized values - Original: '%s.%s' -> Sanitized: '%s.%s'", 
                    device_raw, action_raw, device, action)

        if not event_data:
            _LOGGER.error("Event data is required for save_ir_code service")
            return {"success": False, "error": "Event data is required"}

        try:
            # Parse event_data if it's a string
            if isinstance(event_data, str):
                import json
                try:
                    event_data = json.loads(event_data)
                except json.JSONDecodeError:
                    _LOGGER.error("Invalid JSON in event_data: %s", event_data)
                    return {"success": False, "error": "Invalid JSON in event_data"}            # Check if entry already exists
            db_path = hass.config.path(DB_NAME)
            if check_ir_code_exists(db_path, device, action):
                error_msg = f"IR code for {device_raw}.{action_raw} (sanitized: {device}.{action}) already exists"
                _LOGGER.error(error_msg)
                
                # Fire error event
                event_data_event = {
                    "device": device_raw,  # Use original values for frontend
                    "action": action_raw,
                    "success": False,
                    "error": error_msg
                }
                _LOGGER.info("Firing error event: %s with data: %s", f"{DOMAIN}_code_saved", event_data_event)
                hass.bus.fire(f"{DOMAIN}_code_saved", event_data_event)
                
                return {"success": False, "error": error_msg}

            # Save to database (using sanitized values)
            success = save_ir_code(db_path, device, action, event_data)
            
            if success:
                _LOGGER.info("IR code saved successfully for %s.%s (sanitized: %s.%s)", 
                            device_raw, action_raw, device, action)

                # Fire success event (using original values for frontend)
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
                
                # Fire error event
                hass.bus.fire(f"{DOMAIN}_code_saved", {
                    "device": device_raw, 
                    "action": action_raw,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}

        except Exception as err:
            _LOGGER.error("Failed to save IR code: %s", err)
            
            # Fire error event (using original values for frontend)
            hass.bus.fire(f"{DOMAIN}_code_saved", {
                "device": device_raw, 
                "action": action_raw,
                "success": False,
                "error": str(err)
            })
            
            return {"success": False, "error": str(err)}

    async def handle_delete_ir_code_service(call):
        """Handle the delete_ir_code service call."""
        _LOGGER.info("Service 'delete_ir_code' called with data: %s", call.data)
        code_id = call.data.get("id")

        if not code_id:
            _LOGGER.error("ID is required for delete_ir_code service")
            return {"success": False, "error": "ID is required"}

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
                
                # Fire success event
                hass.bus.fire(f"{DOMAIN}_code_deleted", {
                    "id": code_id,
                    "success": True
                })
                
                return {"success": True, "id": code_id}
            else:
                error_msg = f"No IR code found with ID {code_id}"
                _LOGGER.warning(error_msg)
                
                # Fire error event
                hass.bus.fire(f"{DOMAIN}_code_deleted", {
                    "id": code_id,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}

        except Exception as err:
            _LOGGER.error("Failed to delete IR code: %s", err)
            
            # Fire error event
            hass.bus.fire(f"{DOMAIN}_code_deleted", {
                "id": code_id,
                "success": False,
                "error": str(err)
            })
            
            return {"success": False, "error": str(err)}

    # Register the services
    hass.services.async_register(
        DOMAIN, "get_recent_codes", handle_get_recent_codes_service
    )
    
    hass.services.async_register(
        DOMAIN, "save_ir_code", handle_save_ir_code_service
    )
    
    hass.services.async_register(
        DOMAIN, "delete_ir_code", handle_delete_ir_code_service
    )

    _LOGGER.info("Hassbeam Connect integration setup completed")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Hassbeam Connect integration")

    # Remove services
    hass.services.async_remove(DOMAIN, "get_recent_codes")
    hass.services.async_remove(DOMAIN, "save_ir_code")
    hass.services.async_remove(DOMAIN, "delete_ir_code")

    # Clear data
    hass.data.pop(DOMAIN, None)

    return True


