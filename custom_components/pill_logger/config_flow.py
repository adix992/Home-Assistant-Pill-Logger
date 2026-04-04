import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class PillLoggerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input["medication_name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("medication_name", default="My Medication"): str,
                vol.Required("initial_stock", default=30): int
            })
        )