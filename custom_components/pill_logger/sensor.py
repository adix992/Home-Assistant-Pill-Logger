from homeassistant.components.sensor import RestoreSensor
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    med_name = entry.data["medication_name"]
    async_add_entities([PillTotalSensor(med_name, entry.entry_id)])

class PillTotalSensor(RestoreSensor):
    def __init__(self, name, entry_id):
        self._attr_name = f"{name} Total Doses"
        self._attr_unique_id = f"{entry_id}_total"
        self._attr_icon = "mdi:chart-line"
        self._entry_id = entry_id
        self._state = 0

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_taken_{self._entry_id}", self.increment)
        )
        last_state = await self.async_get_last_sensor_data()
        if last_state and last_state.native_value is not None:
            self._state = int(last_state.native_value)

    @property
    def native_value(self):
        return self._state

    def increment(self):
        self._state += 1
        self.async_write_ha_state()