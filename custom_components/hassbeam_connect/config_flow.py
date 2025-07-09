"""Config flow for Hassbeam Connect integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

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
        self._listening = False
        self._capture_result = None
        self._event_listener = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: Input device and action."""
        errors = {}
        
        if user_input is not None:
            if user_input.get("cancel"):
                return self.async_create_entry(title="", data={})
                
            if user_input.get("next"):
                device = user_input.get("device", "").strip()
                action = user_input.get("action", "").strip()
                
                if not device:
                    errors["device"] = "device_required"
                if not action:
                    errors["action"] = "action_required"
                
                if not errors:
                    # Store values and go to step 2
                    self._device = device
                    self._action = action
                    return self.async_show_form(step_id="capture")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("device", default=self._device): str,
                vol.Required("action", default=self._action): str,
                vol.Optional("next"): bool,
                vol.Optional("cancel"): bool,
            }),
            errors=errors,
            description_placeholders={
                "description": """**IR Code Capture Setup**

Configure which IR code you want to capture:

• **Device**: Name of your device (e.g., "TV", "Soundbar", "AC")
• **Action**: Name of the button/action (e.g., "power", "volume_up", "mute")

Click "Next" to start capturing the IR signal."""
            }
        )

    async def async_step_capture(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: Capture IR code automatically."""
        
        if user_input is not None:
            if user_input.get("add_another"):
                # Reset and go back to step 1
                self._reset_capture_state()
                return self.async_show_form(step_id="init")
                
            if user_input.get("finish"):
                self._cleanup_listener()
                return self.async_create_entry(title="", data={})

        # If not listening yet, start the capture process
        if not self._listening and self._capture_result is None:
            return await self._start_capture()
            
        # Show result with buttons
        if self._capture_result:
            return await self._show_result()
            
        # Show waiting state
        return await self._show_waiting()

    async def _start_capture(self) -> FlowResult:
        """Start the IR capture process."""
        try:
            # Set listening state
            self._listening = True
            self._capture_result = None
            
            # Setup event listener
            self._setup_event_listener()
            
            # Call start_listening service
            await self.hass.services.async_call(
                DOMAIN,
                "start_listening",
                {"device": self._device, "action": self._action},
                blocking=True
            )
            
            return await self._show_waiting()
            
        except Exception as err:
            _LOGGER.error("Failed to start IR capture: %s", err)
            self._listening = False
            self._capture_result = f"❌ Error: Failed to start capture - {err}"
            return await self._show_result()

    def _setup_event_listener(self):
        """Setup event listener for IR capture success."""
        @callback
        def handle_ir_saved(event):
            """Handle IR code saved event."""
            if (event.data.get("device") == self._device and 
                event.data.get("action") == self._action):
                self._listening = False
                self._capture_result = f"✅ Success! IR code for {self._device}.{self._action} has been saved to the database."
                
                # Remove listener
                if self._event_listener:
                    self._event_listener()
                    self._event_listener = None
        
        self._event_listener = self.hass.bus.async_listen(f"{DOMAIN}_saved", handle_ir_saved)

    async def _show_waiting(self) -> FlowResult:
        """Show waiting for IR signal."""
        return self.async_show_form(
            step_id="capture",
            data_schema=vol.Schema({}),  # No buttons while waiting
            description_placeholders={
                "description": f"""**🎯 Listening for IR Signal**

**Device**: {self._device}
**Action**: {self._action}

**Please press the '{self._action}' button on your {self._device} remote control now.**

The system is waiting for the IR signal... This page will automatically update when the signal is received."""
            }
        )

    async def _show_result(self) -> FlowResult:
        """Show capture result with action buttons."""
        return self.async_show_form(
            step_id="capture",
            data_schema=vol.Schema({
                vol.Optional("add_another"): bool,
                vol.Optional("finish"): bool,
            }),
            description_placeholders={
                "description": f"""**Capture Result**

{self._capture_result}

**What would you like to do next?**

• **Add Another Code**: Capture another IR code for a different action
• **Finish**: Complete the configuration and exit"""
            }
        )

    def _reset_capture_state(self):
        """Reset capture state for new capture."""
        self._listening = False
        self._capture_result = None
        self._action = ""  # Clear action for new input
        self._cleanup_listener()

    def _cleanup_listener(self):
        """Remove event listener if active."""
        if self._event_listener:
            self._event_listener()
            self._event_listener = None
