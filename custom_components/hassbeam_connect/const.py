"""
Constants for the HassBeam Connect integration.

This module defines all constants used throughout the HassBeam Connect integration,
including domain names, event types, and configuration parameters.
"""

# Integration domain name used by Home Assistant
DOMAIN = "hassbeam_connect"

# Event type fired by ESPHome HassBeam devices when IR codes are received
IR_EVENT_TYPE = "esphome.hassbeam.ir_received"

# Name of the SQLite database file for storing IR codes
DB_NAME = "hassbeam.db"

# List of event types that the integration listens for
TEST_EVENT_TYPES = [
    "esphome.hassbeam.ir_received",  # Standard HassBeam event
]
