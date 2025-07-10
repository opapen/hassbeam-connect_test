"""Hassbeam Connect integration for Home Assistant."""

import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, IR_EVENT_TYPE, DB_NAME
from .database import init_db, save_ir_code, get_ir_codes
import os
import sqlite3

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
        _LOGGER.warning(
            "DEBUG: IR event handler called! Event: %s, Data: %s",
            event.event_type,
            event.data,
        )

        pending = hass.data[DOMAIN].get("pending")
        if not pending:
            _LOGGER.warning(
                "DEBUG: Received IR event but no capture pending. Event: %s",
                event.event_type,
            )
            return

        device = pending["device"]
        action = pending["action"]
        event_data = event.data

        _LOGGER.info("Capturing IR code for %s.%s", device, action)

        try:
            # Save to database
            save_ir_code(hass.config.path(DB_NAME), device, action, event_data)

            # Fire success event
            hass.bus.fire(f"{DOMAIN}_saved", {"device": device, "action": action})

            # Clear pending state
            hass.data[DOMAIN]["pending"] = None

            _LOGGER.info("IR code saved successfully for %s.%s", device, action)

        except Exception as err:
            _LOGGER.error("Failed to save IR code: %s", err)

    # Listen for IR events from HassBeam device
    hass.bus.async_listen(IR_EVENT_TYPE, handle_ir_event)

    # Debug: Listen to ALL events to see what's actually being sent
    @callback
    def debug_all_events(event):
        """Debug handler to see all events."""
        if "ir" in event.event_type.lower() or "remote" in event.event_type.lower():
            _LOGGER.warning(
                "DEBUG: Received event: %s with data: %s", event.event_type, event.data
            )

    hass.bus.async_listen("*", debug_all_events)

    async def handle_start_listening_service(call):
        """Handle the start_listening service call."""
        device = call.data.get("device", "").strip()
        action = call.data.get("action", "").strip()

        if not device:
            _LOGGER.error("Device is required")
            return

        if not action:
            _LOGGER.error("Action is required")
            return

        _LOGGER.info("Starting to listen for IR code: %s.%s", device, action)
        hass.data[DOMAIN]["pending"] = {"device": device, "action": action}

    # Register the service
    hass.services.async_register(
        DOMAIN, "start_listening", handle_start_listening_service
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
                formatted_codes.append(
                    {
                        "id": code[0],
                        "device": code[1],
                        "action": code[2],
                        "event_data": code[3],
                        "created_at": code[4],
                    }
                )

            # Log the results for debugging
            _LOGGER.info("Retrieved %d IR codes from database", len(formatted_codes))
            for code in formatted_codes:
                _LOGGER.info(
                    "Code: %s.%s (ID: %s) - Created: %s",
                    code["device"],
                    code["action"],
                    code["id"],
                    code["created_at"]
                )

            # Fire event with the codes
            hass.bus.fire(f"{DOMAIN}_codes_retrieved", {"codes": formatted_codes})

            # Show notification with results
            if formatted_codes:
                message = f"Found {len(formatted_codes)} IR codes:\n"
                for code in formatted_codes[:5]:  # Show first 5
                    message += f"• {code['device']}.{code['action']} ({code['created_at']})\n"
                if len(formatted_codes) > 5:
                    message += f"... and {len(formatted_codes) - 5} more"
            else:
                message = "No IR codes found in database"
                if device:
                    message += f" for device '{device}'"

            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Hassbeam Connect - Recent Codes",
                    "message": message,
                    "notification_id": "hassbeam_connect_recent_codes",
                },
                blocking=False,
            )

            # Return for service response
            return {"codes": formatted_codes}

        except Exception as err:
            _LOGGER.error("Failed to retrieve IR codes: %s", err)
            # Show error notification
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Hassbeam Connect - Error",
                    "message": f"Failed to retrieve IR codes: {err}",
                    "notification_id": "hassbeam_connect_error",
                },
                blocking=False,
            )
            return {"codes": []}

    # Register the new service
    hass.services.async_register(
        DOMAIN, "get_recent_codes", handle_get_recent_codes_service
    )

    async def handle_debug_database_service(call):
        """Debug service to check database status."""
        try:
            db_path = hass.config.path(DB_NAME)
            
            # Check if database file exists
            if not os.path.exists(db_path):
                message = f"Database file does not exist: {db_path}"
                _LOGGER.warning(message)
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Database Debug",
                        "message": message,
                        "notification_id": "hassbeam_debug",
                    },
                    blocking=False,
                )
                return
            
            # Check database content
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ir_codes")
                count = cursor.fetchone()[0]
                
                cursor.execute("SELECT * FROM ir_codes ORDER BY created_at DESC LIMIT 3")
                recent = cursor.fetchall()
                
                message = f"Database: {db_path}\n"
                message += f"Total IR codes: {count}\n\n"
                
                if recent:
                    message += "Recent codes:\n"
                    for code in recent:
                        message += f"• {code[1]}.{code[2]} ({code[4]})\n"
                else:
                    message += "No codes found in database"
                
                _LOGGER.info("Database debug: %s", message)
                
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Database Debug",
                        "message": message,
                        "notification_id": "hassbeam_debug",
                    },
                    blocking=False,
                )
                
        except Exception as err:
            _LOGGER.error("Database debug failed: %s", err)

    # Register the debug service
    hass.services.async_register(
        DOMAIN, "debug_database", handle_debug_database_service
    )

    _LOGGER.info("Hassbeam Connect integration setup completed")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Hassbeam Connect integration")

    # Remove services
    hass.services.async_remove(DOMAIN, "start_listening")
    hass.services.async_remove(DOMAIN, "get_recent_codes")
    hass.services.async_remove(DOMAIN, "debug_database")

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
                "notification_id": "hassbeam_connect_setup",
            },
            blocking=False,
        )
    except Exception as err:
        _LOGGER.debug("Could not show setup notification: %s", err)
