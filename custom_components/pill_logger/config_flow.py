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
            elif user_input["tracking_type"] == "Time of Day":
                return await self.async_step_time_of_day()
            else:
                return await self.async_step_as_needed()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("medication_name", default="My Medication"): str,
                vol.Required("tracking_type", default="Regular Interval"): vol.In(["Regular Interval", "Time of Day", "As Needed"])
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
                vol.Required("hours_between_doses", default=8): int,
                vol.Required("safe_doses", default=1): int
            })
        )

    async def async_step_time_of_day(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data["medication_name"], data=self._data)

        return self.async_show_form(
            step_id="time_of_day",
            data_schema=vol.Schema({
                vol.Required("initial_stock", default=30): int,
                vol.Required("time_of_day", default="08:00"): str,
                vol.Required("safe_doses", default=1): int
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
                vol.Required("safe_doses", default=2): int,
                vol.Required("time_window_hours", default=8): int
            })
        )
