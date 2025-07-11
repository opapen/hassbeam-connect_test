"""
HassBeam Connect Integration for Home Assistant

This custom integration provides a bridge between HassBeam IR devices and Home Assistant,
allowing users to capture, store, and manage IR codes from their remote controls.

Services provided:
- get_recent_codes: Retrieve captured IR codes with optional filtering
- save_ir_code: Store IR codes with device and action names
- delete_ir_code: Remove codes from the database
- send_ir_code: Send stored IR codes via HassBeam device
"""

import json
import logging
import re
import unicodedata
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, DB_NAME
from .database import init_db, get_ir_codes, save_ir_code, check_ir_code_exists, delete_ir_code, get_ir_code_by_device_action

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


def _get_protocol_service_mapping():
    """Get the mapping of protocols to their service names and required parameters."""
    return {
        "AEHA": {
            "service": "send_ir_aeha",
            "params": ["address", "data", "carrier_frequency"]
        },
        "Beo4": {
            "service": "send_ir_beo4", 
            "params": ["source", "command"]
        },
        "JVC": {
            "service": "send_ir_jvc",
            "params": ["data"]
        },
        "Haier": {
            "service": "send_ir_haier",
            "params": ["code"]
        },
        "LG": {
            "service": "send_ir_lg",
            "params": ["data", "nbits"]
        },
        "NEC": {
            "service": "send_ir_nec",
            "params": ["address", "command", "command_repeats"]
        },
        "Panasonic": {
            "service": "send_ir_panasonic",
            "params": ["address", "command"]
        },
        "Pioneer": {
            "service": "send_ir_pioneer",
            "params": ["rc_code_1", "rc_code_2", "repeat_times"]
        },
        "Pioneer Simple": {
            "service": "send_ir_pioneer_simple",
            "params": ["rc_code_1"]
        },
        "Pronto": {
            "service": "send_ir_pronto",
            "params": ["data"]
        },
        "Raw": {
            "service": "send_ir_raw",
            "params": ["data", "freq"]
        },
        "RC5": {
            "service": "send_ir_rc5",
            "params": ["address", "command"]
        },
        "RC6": {
            "service": "send_ir_rc6",
            "params": ["address", "command"]
        },
        "Roomba": {
            "service": "send_ir_roomba",
            "params": ["data", "repeat_times", "wait_time_ms"]
        },
        "Samsung": {
            "service": "send_ir_samsung",
            "params": ["data", "nbits"]
        },
        "Samsung36": {
            "service": "send_ir_samsung36",
            "params": ["address", "command"]
        },
        "Sony": {
            "service": "send_sony",
            "params": ["data", "nbits"]
        },
        "Toshiba AC": {
            "service": "send_toshiba_ac",
            "params": ["rc_code_1", "rc_code_2"]
        }
    }


def _convert_hex_strings_to_int(value):
    """Convert hex string values to integers."""
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, 16)
    return value


def _parse_array_string(array_str):
    """Parse array string format like '[ 1, 2, 3, ... ]' into a list of integers."""
    if isinstance(array_str, str) and array_str.startswith("[ ") and array_str.endswith(" ]"):
        # Remove brackets and split by comma
        content = array_str[2:-2].strip()
        if content:
            return [int(x.strip()) for x in content.split(",") if x.strip()]
    return array_str


def _prepare_service_data(protocol, event_data):
    """Prepare service data for the specific protocol."""
    protocol_mapping = _get_protocol_service_mapping()
    
    if protocol not in protocol_mapping:
        raise ValueError(f"Unsupported protocol: {protocol}")
    
    service_info = protocol_mapping[protocol]
    service_data = {}
    
    # Default values for common parameters
    defaults = {
        "nbits": 32,  # Default for Samsung
        "command_repeats": 1,  # Default for NEC
        "repeat_times": 3,  # Default for Roomba
        "wait_time_ms": 17,  # Default for Roomba
        "freq": 38000,  # Default for Raw
        "carrier_frequency": 38000  # Default for AEHA
    }
    
    for param in service_info["params"]:
        if param in event_data:
            value = event_data[param]
            
            # Handle array parameters for AEHA, Haier, and Raw protocols
            if param in ["data", "code"] and protocol in ["AEHA", "Haier", "Raw"]:
                value = _parse_array_string(value)
            # Convert hex strings to integers for numeric parameters
            elif param in ["address", "command", "data", "rc_code_1", "rc_code_2", "source"]:
                value = _convert_hex_strings_to_int(value)
            
            service_data[param] = value
        elif param in defaults:
            # Use default value if parameter is missing but has a default
            service_data[param] = defaults[param]
    
    return service_info["service"], service_data


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

    async def handle_send_ir_code(call):
        """Handle send_ir_code service."""
        _LOGGER.info("Service 'send_ir_code' called with data: %s", call.data)
        
        # Extract parameters
        device_raw = call.data.get("device", "").strip()
        action_raw = call.data.get("action", "").strip()
        hassbeam_device = call.data.get("hassbeam_device", "").strip()

        # Validate required parameters
        if not device_raw:
            _LOGGER.error("Device is required")
            return {"success": False, "error": "Device is required"}
        
        if not action_raw:
            _LOGGER.error("Action is required")
            return {"success": False, "error": "Action is required"}

        # Sanitize parameters for database lookup
        device = sanitize_string(device_raw)
        action = sanitize_string(action_raw)
        
        _LOGGER.info("Looking up IR code - Original: '%s.%s' -> Sanitized: '%s.%s'", 
                    device_raw, action_raw, device, action)

        try:
            # Look up the IR code in the database
            db_path = hass.config.path(DB_NAME)
            ir_code = get_ir_code_by_device_action(db_path, device, action)
            
            if not ir_code:
                error_msg = f"No IR code found for {device_raw}.{action_raw}"
                _LOGGER.error(error_msg)
                
                _fire_event(hass, f"{DOMAIN}_code_sent", {
                    "device": device_raw,
                    "action": action_raw,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}

            # Prepare service call data
            event_data = ir_code["event_data"]
            protocol = event_data.get("protocol")
            
            if not protocol:
                error_msg = f"No protocol found in event data for {device_raw}.{action_raw}"
                _LOGGER.error(error_msg)
                
                _fire_event(hass, f"{DOMAIN}_code_sent", {
                    "device": device_raw,
                    "action": action_raw,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}
            
            try:
                # Get the service name and prepare parameters for the specific protocol
                service_name, service_data = _prepare_service_data(protocol, event_data)
                
                # Determine the service domain
                if hassbeam_device:
                    service_domain = f"esphome.{hassbeam_device}"
                else:
                    # Use default device name
                    service_domain = "esphome.hassbeam"
                
                _LOGGER.info("Calling service %s.%s with data: %s", service_domain, service_name, service_data)
                
                # Call the protocol-specific service
                await hass.services.async_call(service_domain, service_name, service_data)
                
            except ValueError as err:
                error_msg = f"Protocol error for {device_raw}.{action_raw}: {str(err)}"
                _LOGGER.error(error_msg)
                
                _fire_event(hass, f"{DOMAIN}_code_sent", {
                    "device": device_raw,
                    "action": action_raw,
                    "success": False,
                    "error": error_msg
                })
                
                return {"success": False, "error": error_msg}
            
            _LOGGER.info("IR code sent successfully for %s.%s", device_raw, action_raw)
            
            _fire_event(hass, f"{DOMAIN}_code_sent", {
                "device": device_raw,
                "action": action_raw,
                "success": True,
                "hassbeam_device": hassbeam_device or None
            })
            
            return {
                "success": True, 
                "device": device_raw, 
                "action": action_raw,
                "hassbeam_device": hassbeam_device or None
            }

        except Exception as err:
            _LOGGER.error("Failed to send IR code: %s", err)
            
            _fire_event(hass, f"{DOMAIN}_code_sent", {
                "device": device_raw,
                "action": action_raw,
                "success": False,
                "error": str(err)
            })
            
            return {"success": False, "error": str(err)}

    # Register all services
    hass.services.async_register(DOMAIN, "get_recent_codes", handle_get_recent_codes)
    hass.services.async_register(DOMAIN, "save_ir_code", handle_save_ir_code)
    hass.services.async_register(DOMAIN, "delete_ir_code", handle_delete_ir_code)
    hass.services.async_register(DOMAIN, "send_ir_code", handle_send_ir_code)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up resources."""
    _LOGGER.debug("Unloading HassBeam Connect integration")

    # Remove all registered services
    services = ["get_recent_codes", "save_ir_code", "delete_ir_code", "send_ir_code"]
    for service in services:
        hass.services.async_remove(DOMAIN, service)

    # Clear stored data
    hass.data.pop(DOMAIN, None)

    _LOGGER.info("HassBeam Connect integration unloaded successfully")
    return True


