"""Hassbeam Connect integration for Home Assistant."""

import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, DB_NAME
from .database import init_db, get_ir_codes, save_ir_code

_LOGGER = logging.getLogger(__name__)


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
        device = call.data.get("device")
        limit = call.data.get("limit", 10)

        try:
            db_path = hass.config.path(DB_NAME)
            codes = get_ir_codes(db_path, device, limit)

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
        device = call.data.get("device", "").strip()
        action = call.data.get("action", "").strip()
        event_data = call.data.get("event_data", "")

        if not device:
            _LOGGER.error("Device is required for save_ir_code service")
            return {"success": False, "error": "Device is required"}

        if not action:
            _LOGGER.error("Action is required for save_ir_code service")
            return {"success": False, "error": "Action is required"}

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
                    return {"success": False, "error": "Invalid JSON in event_data"}

            # Save to database
            db_path = hass.config.path(DB_NAME)
            save_ir_code(db_path, device, action, event_data)

            _LOGGER.info("IR code saved successfully for %s.%s", device, action)

            # Fire success event
            hass.bus.fire(f"{DOMAIN}_code_saved", {
                "device": device, 
                "action": action,
                "success": True
            })

            return {"success": True, "device": device, "action": action}

        except Exception as err:
            _LOGGER.error("Failed to save IR code: %s", err)
            
            # Fire error event
            hass.bus.fire(f"{DOMAIN}_code_saved", {
                "device": device, 
                "action": action,
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

    _LOGGER.info("Hassbeam Connect integration setup completed")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Hassbeam Connect integration")

    # Remove services
    hass.services.async_remove(DOMAIN, "get_recent_codes")
    hass.services.async_remove(DOMAIN, "save_ir_code")

    # Clear data
    hass.data.pop(DOMAIN, None)

    return True


