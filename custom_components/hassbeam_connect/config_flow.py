"""
Configuration flow for HassBeam Connect integration.

This module handles the configuration flow for the HassBeam Connect integration,
allowing users to set up the integration through the Home Assistant UI.

The integration uses a simple setup flow since it doesn't require external
configuration parameters - it works automatically with HassBeam devices
that are already configured in ESPHome.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Schema for the configuration form (empty since no configuration is needed)
STEP_USER_DATA_SCHEMA = vol.Schema({})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the configuration flow for HassBeam Connect integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Handle the initial configuration step.
        
        Since HassBeam Connect doesn't require any configuration parameters,
        this flow simply creates the integration entry. The integration
        automatically detects and works with HassBeam devices configured
        in ESPHome.
        
        Args:
            user_input: User input from the configuration form (unused)
            
        Returns:
            FlowResult: Either shows the configuration form or creates the entry
        """
        # Ensure only one instance of the integration is configured
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
            
        # If user has submitted the form, create the integration entry
        if user_input is not None:
            return self.async_create_entry(
                title="HassBeam Connect", 
                data={}
            )

        # Show the configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={
                "name": "HassBeam Connect",
            },
        )
