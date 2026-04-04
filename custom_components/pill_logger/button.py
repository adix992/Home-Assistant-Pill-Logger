from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    med_name = entry.data["medication_name"]
    async_add_entities([PillTakeButton(med_name, entry.entry_id)])

class PillTakeButton(ButtonEntity):
    def __init__(self, name, entry_id):
        self._name = name
        self._attr_name = f"Take {name}"
        self._attr_unique_id = f"{entry_id}_take"
        self._attr_icon = "mdi:pill"
        self._entry_id = entry_id

    async def async_press(self):
        """When pressed, send a signal to update the sensor and number entities."""
        safe_doses_entity_id = f"sensor.{self._name.lower().replace(' ', '_')}_safe_doses"
        
        state = self.hass.states.get(safe_doses_entity_id)
        if state is not None and str(state.state) == "0":
            raise HomeAssistantError("WARNING: Safe dosage limit exceeded. Cannot log pill.")
            
        async_dispatcher_send(self.hass, f"pill_taken_{self._entry_id}")
