import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class PillLoggerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self):
        self._data = {}

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            if user_input["tracking_type"] == "Regular Interval":
                return await self.async_step_regular_interval()
            else:
                return await self.async_step_as_needed()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("medication_name", default="My Medication"): str,
                vol.Required("tracking_type", default="Regular Interval"): vol.In(["Regular Interval", "As Needed"])
            })
        )

    async def async_step_regular_interval(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data["medication_name"], data=self._data)

        return self.async_show_form(
            step_id="regular_interval",
            data_schema=vol.Schema({
                vol.Required("initial_stock", default=30): int,
                vol.Required("hours_between_doses", default=8): int
            })
        )

    async def async_step_as_needed(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data["medication_name"], data=self._data)

        return self.async_show_form(
            step_id="as_needed",
            data_schema=vol.Schema({
                vol.Required("initial_stock", default=30): int,
                vol.Required("max_pills_allowed", default=2): int,
                vol.Required("time_window_hours", default=8): int
            })
        )
