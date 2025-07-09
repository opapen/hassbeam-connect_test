"""Config flow for Hassbeam Connect integration."""
from __future__ import annotations

import logging
from typing import Any
import asyncio

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Optional("device_name", default="TV"): str,
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hassbeam Connect."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
            
        if user_input is not None:
            device_name = user_input.get("device_name", "TV").strip()
            
            if not device_name:
                return self.async_show_form(
                    step_id="user",
                    data_schema=STEP_USER_DATA_SCHEMA,
                    errors={"device_name": "device_name_required"},
                )
            
            return self.async_create_entry(
                title=f"Hassbeam Connect ({device_name})", 
                data={"device_name": device_name}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for IR code management."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._device = ""
        self._action = ""
        self._success_message = None
        self._listening = False

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage IR code capture."""
        errors = {}
        
        if user_input is not None:
            device = user_input.get("device", "").strip()
            action = user_input.get("action", "").strip()
            
            # Store current values
            self._device = device
            self._action = action
            
            # Check if start listening was triggered
            if user_input.get("submit") == "start_listening":
                if not device:
                    errors["device"] = "device_required"
                if not action:
                    errors["action"] = "action_required"
                
                if not errors:
                    # Start listening
                    self._listening = True
                    self._success_message = None
                    
                    # Call start_listening service
                    await self.hass.services.async_call(
                        DOMAIN,
                        "start_listening",
                        {"device": device, "action": action}
                    )
                    
                    # Listen for success event
                    self._setup_event_listener()
                    
                    return await self._show_capture_form(
                        waiting_message=f"Waiting for IR signal for {device}.{action}...",
                        device=device,
                        action="",  # Clear action field after starting
                        listening=True
                    )

        return await self._show_capture_form()

    def _setup_event_listener(self):
        """Setup event listener for IR capture success."""
        @callback
        def handle_ir_saved(event):
            """Handle IR code saved event."""
            if (event.data.get("device") == self._device and 
                event.data.get("action") == self._action):
                self._listening = False
                self._success_message = f"✅ IR code for {self._device}.{self._action} saved successfully!"
                self._action = ""  # Clear action field
                
                # Remove listener
                self.hass.bus.async_remove_listener(f"{DOMAIN}_saved", handle_ir_saved)
        
        self.hass.bus.async_listen(f"{DOMAIN}_saved", handle_ir_saved)

    async def _show_capture_form(
        self, 
        waiting_message: str = None, 
        device: str = None, 
        action: str = None,
        listening: bool = None
    ) -> FlowResult:
        """Show the IR capture form."""
        if device is None:
            device = self._device
        if action is None:
            action = self._action
        if listening is None:
            listening = self._listening
            
        # Build description
        description = """**IR Code Capture**

Use this interface to capture and store IR codes from your remote controls.

1. Enter the device name (e.g., "TV", "Soundbar", "AC")
2. Enter the action name (e.g., "power", "volume_up", "channel_1")
3. Click "Start Listening" and then press the button on your remote
4. The IR code will be automatically saved to the database

**Note:** Make sure your HassBeam device is connected and working."""

        if waiting_message:
            description += f"\n\n🎯 **{waiting_message}**"
        
        if self._success_message:
            description += f"\n\n{self._success_message}"

        # Build schema - always show fields and button
        schema_dict = {
            vol.Required("device", default=device): str,
            vol.Required("action", default=action): str,
        }
        
        # Add submit button - enabled/disabled based on state
        can_start = bool(device and action and not listening)
        if can_start:
            schema_dict[vol.Required("submit", default="start_listening")] = vol.In(["start_listening"])
        else:
            # Show disabled button by using optional with fixed value
            schema_dict[vol.Optional("submit_disabled", default="Start Listening (fill fields first)")] = str

        schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors={},
            description_placeholders={
                "description": description
            }
        )
