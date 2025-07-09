"""Hassbeam Connect integration for Home Assistant."""
import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, IR_EVENT_TYPE, DB_NAME
from .database import init_db, save_ir_code, get_ir_codes

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hassbeam Connect from a config entry."""
    _LOGGER.debug("Setting up Hassbeam Connect integration")
    
    # Store config data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = entry.data
    
    # Automatische Frontend-Resource-Registrierung
    await _register_frontend_resource(hass)
    
    # Initialize database
    try:
        db_path = hass.config.path(DB_NAME)
        init_db(db_path)
        _LOGGER.info("Database initialized successfully: %s", db_path)
    except Exception as err:
        _LOGGER.error("Failed to initialize database: %s", err)
        return False

    # No pending IR capture by default
    hass.data[DOMAIN]["pending"] = None

    @callback
    def handle_ir_event(event):
        """Handle incoming IR events from HassBeam device."""
        pending = hass.data[DOMAIN].get("pending")
        if not pending:
            _LOGGER.debug("Received IR event but no capture pending")
            return

        device = pending["device"]
        action = pending["action"]
        event_data = event.data

        _LOGGER.info("Capturing IR code for %s.%s", device, action)
        
        try:
            # Save to database
            save_ir_code(hass.config.path(DB_NAME), device, action, event_data)
            
            # Fire success event
            hass.bus.fire(f"{DOMAIN}_saved", {
                "device": device, 
                "action": action
            })
            
            # Clear pending state
            hass.data[DOMAIN]["pending"] = None
            
            _LOGGER.info("IR code saved successfully for %s.%s", device, action)
            
        except Exception as err:
            _LOGGER.error("Failed to save IR code: %s", err)

    # Listen for IR events from HassBeam device
    hass.bus.async_listen(IR_EVENT_TYPE, handle_ir_event)

    async def handle_start_listening_service(call):
        """Handle the start_listening service call."""
        config = hass.data[DOMAIN]["config"]
        device = call.data.get("device") or config.get("device_name", "TV")
        action = call.data.get("action", "").strip()
        
        if not action:
            _LOGGER.error("Action is required")
            return
            
        _LOGGER.info("Starting to listen for IR code: %s.%s", device, action)
        hass.data[DOMAIN]["pending"] = {"device": device, "action": action}

    # Register the service
    hass.services.async_register(
        DOMAIN, 
        "start_listening", 
        handle_start_listening_service
    )

    async def handle_get_recent_codes_service(call):
        """Handle the get_recent_codes service call."""
        device = call.data.get("device")
        limit = call.data.get("limit", 10)
        
        try:
            db_path = hass.config.path(DB_NAME)
            codes = get_ir_codes(db_path, device, limit)
            
            # Convert to a more user-friendly format
            formatted_codes = []
            for code in codes:
                formatted_codes.append({
                    "id": code[0],
                    "device": code[1],
                    "action": code[2],
                    "created_at": code[4]
                })
            
            # Fire event with the codes
            hass.bus.fire(f"{DOMAIN}_codes_retrieved", {
                "codes": formatted_codes
            })
            
            return formatted_codes
            
        except Exception as err:
            _LOGGER.error("Failed to retrieve IR codes: %s", err)
            return []

    # Register the new service
    hass.services.async_register(
        DOMAIN, 
        "get_recent_codes", 
        handle_get_recent_codes_service
    )

    _LOGGER.info("Hassbeam Connect integration setup completed")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Hassbeam Connect integration")
    
    # Remove services
    hass.services.async_remove(DOMAIN, "start_listening")
    hass.services.async_remove(DOMAIN, "get_recent_codes")
    
    # Clear data
    hass.data.pop(DOMAIN, None)
    
    return True


async def _register_frontend_resource(hass: HomeAssistant) -> None:
    """Show setup notification to user."""
    try:
        message = """🎉 Hassbeam Connect successfully installed!

Services available:
- hassbeam_connect.start_listening
- hassbeam_connect.get_recent_codes

Check documentation for usage examples."""
            
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Hassbeam Connect Ready",
                "message": message,
                "notification_id": "hassbeam_connect_setup"
            },
            blocking=False
        )
    except Exception as err:
        _LOGGER.debug("Could not show setup notification: %s", err)