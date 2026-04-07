import asyncio
from homeassistant.components.number import RestoreNumber, NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    med_name = entry.data["medication_name"]
    initial_stock = entry.data["initial_stock"]
    async_add_entities([
        PillStockNumber(med_name, entry.entry_id, initial_stock),
        PillAddStockNumber(med_name, entry.entry_id)
    ])

class PillStockNumber(RestoreNumber):
    def __init__(self, name, entry_id, initial_stock):
        self._med_name = name
        self._attr_name = f"{name} Pills Left"
        self._attr_unique_id = f"{entry_id}_stock"
        self._attr_icon = "mdi:medical-bag"
        self._entry_id = entry_id
        self._attr_native_value = float(initial_stock)
        self._attr_native_step = 1.0
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 5000.0
        self._attr_mode = NumberMode.BOX

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._med_name,
            manufacturer="Pill Logger",
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_taken_{self._entry_id}", self.decrement)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_add_stock_{self._entry_id}", self.add_stock)
        )
        last_state = await self.async_get_last_number_data()
        if last_state and last_state.native_value is not None:
            self._attr_native_value = last_state.native_value

    async def async_set_native_value(self, value: float):
        self._attr_native_value = value
        self.async_write_ha_state()

    def decrement(self, *args, **kwargs):
        if self._attr_native_value > 0:
            self._attr_native_value -= 1
            self.async_write_ha_state()

    def add_stock(self, amount: float, *args, **kwargs):
        self._attr_native_value += amount
        self.async_write_ha_state()

class PillAddStockNumber(NumberEntity):
    def __init__(self, name, entry_id):
        self._med_name = name
        self._attr_name = f"Add {name} Refill"
        self._attr_unique_id = f"{entry_id}_add_stock"
        self._attr_icon = "mdi:plus-box"
        self._entry_id = entry_id
        self._attr_native_value = 0.0
        self._attr_native_step = 1.0
        self._attr_native_min_value = 0.0
        self._attr_mode = NumberMode.BOX

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._med_name,
            manufacturer="Pill Logger",
        )

    async def async_set_native_value(self, value: float):
        if value > 0:
            # 1. Update this entity's state so HA registers a change
            self._attr_native_value = value
            self.async_write_ha_state()
            
            # 2. Tell the main inventory to add the stock
            async_dispatcher_send(self.hass, f"pill_add_stock_{self._entry_id}", value)
            
            # 3. Pause for half a second so the UI has time to refresh
            await asyncio.sleep(0.5)
            
            # 4. Quietly reset back to 0
            self._attr_native_value = 0.0
            self.async_write_ha_state()
