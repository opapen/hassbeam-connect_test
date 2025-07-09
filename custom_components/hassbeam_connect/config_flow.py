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
    vol.Optional("database_retention_days", default=30): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=365)
    ),
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hassbeam Connect."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
            
        if user_input is not None:
            device_name = user_input.get("device_name", "TV").strip()
            retention_days = user_input.get("database_retention_days", 30)
            
            if not device_name:
                errors["device_name"] = "device_name_required"
            
            if not errors:
                return self.async_create_entry(
                    title=f"Hassbeam Connect ({device_name})", 
                    data={
                        "device_name": device_name,
                        "database_retention_days": retention_days,
                    }
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Hassbeam Connect."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}
        
        if user_input is not None:
            device_name = user_input.get("device_name", "TV").strip()
            retention_days = user_input.get("database_retention_days", 30)
            
            if not device_name:
                errors["device_name"] = "device_name_required"
            
            if not errors:
                new_data = {
                    "device_name": device_name,
                    "database_retention_days": retention_days,
                }
                
                if device_name != self.config_entry.data.get("device_name"):
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, 
                        title=f"Hassbeam Connect ({device_name})"
                    )
                
                return self.async_create_entry(title="", data=new_data)

        current_data = self.config_entry.data
        schema = vol.Schema({
            vol.Optional(
                "device_name", 
                default=current_data.get("device_name", "TV")
            ): str,
            vol.Optional(
                "database_retention_days", 
                default=current_data.get("database_retention_days", 30)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=365)),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
