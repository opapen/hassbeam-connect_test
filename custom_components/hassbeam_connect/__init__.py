"""Hassbeam Connect integration for Home Assistant."""
import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import discovery
from .const import DOMAIN, IR_EVENT_TYPE, DB_NAME
from .database import init_db, save_ir_code

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hassbeam Connect from a config entry."""
    _LOGGER.debug("Setting up Hassbeam Connect integration")
    
    # Initialize domain data
    hass.data.setdefault(DOMAIN, {})
    
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
        device = call.data.get("device", "").strip()
        action = call.data.get("action", "").strip()
        
        if not device or not action:
            _LOGGER.error("Device and action are required")
            return
            
        _LOGGER.info("Starting to listen for IR code: %s.%s", device, action)
        hass.data[DOMAIN]["pending"] = {"device": device, "action": action}

    # Register the service
    hass.services.async_register(
        DOMAIN, 
        "start_listening", 
        handle_start_listening_service
    )

    _LOGGER.info("Hassbeam Connect integration setup completed")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Hassbeam Connect integration")
    
    # Remove service
    hass.services.async_remove(DOMAIN, "start_listening")
    
    # Clear data
    hass.data.pop(DOMAIN, None)
    
    return True


async def _register_frontend_resource(hass: HomeAssistant) -> None:
    """Register the frontend resource automatically."""
    try:
        # HACS-Installation: Datei liegt in hacsfiles
        hacs_path = "/hacsfiles/hassbeam-connect/hassbeam-card.js"
        local_path = "/local/hassbeam-card.js"
        
        # Prüfen welcher Pfad existiert
        import aiohttp
        import asyncio
        
        try:
            # Test HACS-Pfad
            session = aiohttp.ClientSession()
            async with session.get(f"http://localhost:8123{hacs_path}") as response:
                if response.status == 200:
                    resource_url = hacs_path
                    _LOGGER.info("✅ HACS Frontend resource found: %s", hacs_path)
                else:
                    resource_url = local_path
                    _LOGGER.info("✅ Local Frontend resource found: %s", local_path)
            await session.close()
        except:
            # Fallback zu local path
            resource_url = local_path
            
        # Benutzer über korrekte URL informieren
        message = f"""🎉 Hassbeam Connect installiert!

**Karte hinzufügen:**
1. Dashboard bearbeiten → Add Card → Manual
2. YAML: `type: custom:hassbeam-connect-card`

**Falls Karte nicht lädt, Resource manuell hinzufügen:**
- Settings → Dashboards → Resources → Add Resource
- URL: `{resource_url}`
- Type: JavaScript Module

**HACS-Benutzer:** Die Resource wird automatisch von HACS verwaltet."""
            
        try:
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Hassbeam Connect bereit!",
                    "message": message,
                    "notification_id": "hassbeam_connect_ready"
                },
                blocking=False
            )
        except Exception:
            pass  # Notification ist optional
            
    except Exception as err:
        _LOGGER.warning("Could not auto-register frontend resource: %s", err)
        _LOGGER.info("HACS users: The resource should be automatically managed by HACS")
