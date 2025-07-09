"""Config flow for Hassbeam Connect integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage IR code capture."""
        errors = {}
        
        if user_input is not None:
            device = user_input.get("device", "").strip()
            action = user_input.get("action", "").strip()
            
            # Check if start listening was triggered
            if user_input.get("start_listening"):
                if not device:
                    errors["device"] = "device_required"
                if not action:
                    errors["action"] = "action_required"
                
                if not errors:
                    try:
                        # Call start_listening service
                        await self.hass.services.async_call(
                            DOMAIN,
                            "start_listening",
                            {"device": device, "action": action},
                            blocking=True
                        )
                        
                        # Show success message
                        return self.async_show_form(
                            step_id="init",
                            data_schema=self._get_schema(device, ""),
                            description_placeholders={
                                "message": f"✅ Started listening for {device}.{action} - press your remote button now!"
                            }
                        )
                    except Exception as err:
                        _LOGGER.error("Failed to call start_listening service: %s", err)
                        errors["base"] = "service_call_failed"

        # Show the form
        return self.async_show_form(
            step_id="init",
            data_schema=self._get_schema(
                user_input.get("device", "") if user_input else "",
                user_input.get("action", "") if user_input else ""
            ),
            errors=errors,
            description_placeholders={
                "message": "Enter device and action names, then click Start Listening."
            }
        )

    def _get_schema(self, device: str = "", action: str = "") -> vol.Schema:
        """Get the form schema."""
        return vol.Schema({
            vol.Required("device", default=device): str,
            vol.Required("action", default=action): str,
            vol.Optional("start_listening"): bool,
        })
