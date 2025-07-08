from homeassistant.core import HomeAssistant, callback
from .const import DOMAIN, IR_EVENT_TYPE, DB_NAME
from .database import init_db, save_ir_code


async def async_setup_entry(hass: HomeAssistant, entry):
    hass.data.setdefault(DOMAIN, {})
    init_db(hass.config.path(DB_NAME))

    hass.data[DOMAIN]["pending"] = None  # Zustand zum Warten auf das nächste Event

    @callback
    def handle_ir_event(event):
        pending = hass.data[DOMAIN].get("pending")
        if not pending:
            return

        device, action = pending["device"], pending["action"]
        event_data = event.data

        save_ir_code(hass.config.path(DB_NAME), device, action, event_data)

        hass.bus.fire(f"{DOMAIN}_saved", {"device": device, "action": action})
        hass.data[DOMAIN]["pending"] = None

    hass.bus.async_listen(IR_EVENT_TYPE, handle_ir_event)

    async def handle_service(call):
        device = call.data["device"]
        action = call.data["action"]
        hass.data[DOMAIN]["pending"] = {"device": device, "action": action}

    hass.services.async_register(DOMAIN, "start_listening", handle_service)

    return True
