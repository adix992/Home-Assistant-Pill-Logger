from datetime import timedelta
from homeassistant.components.sensor import RestoreSensor, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import homeassistant.util.dt as dt_util
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    med_name = entry.data["medication_name"]
    entities = [PillTotalSensor(med_name, entry.entry_id)]
    entities.append(PillSafeDosesSensor(entry))
    entities.append(PillNextDoseSensor(entry))
    async_add_entities(entities)

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

class PillSafeDosesSensor(RestoreSensor):
    def __init__(self, entry):
        med_name = entry.data["medication_name"]
        self._attr_name = f"{med_name} Safe Doses"
        self._attr_unique_id = f"{entry.entry_id}_safe_doses"
        self._attr_icon = "mdi:pill"
        self._entry_id = entry.entry_id
        self._tracking_type = entry.data.get("tracking_type")
        self._max_pills = entry.data.get("max_pills_allowed", 0)
        self._time_window = entry.data.get("time_window_hours", 0)
        
        self._timestamps = []
        self._attr_extra_state_attributes = {"timestamps": []}
        self._attr_native_value = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_taken_{self._entry_id}", self.pill_taken)
        )
            
        last_state_obj = await self.async_get_last_state()
        if last_state_obj and "timestamps" in last_state_obj.attributes:
            saved_timestamps = last_state_obj.attributes["timestamps"]
            for ts_str in saved_timestamps:
                dt = dt_util.parse_datetime(ts_str)
                if dt:
                    self._timestamps.append(dt)
        self._update_state()

    def pill_taken(self):
        self._timestamps.append(dt_util.now())
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        now = dt_util.now()
        
        if self._tracking_type == "As Needed":
            cutoff = now - timedelta(hours=self._time_window)
            self._timestamps = [ts for ts in self._timestamps if ts >= cutoff]
            self._attr_native_value = max(0, self._max_pills - len(self._timestamps))
            
        self._attr_extra_state_attributes = {
            "timestamps": [ts.isoformat() for ts in self._timestamps]
        }

    @property
    def native_value(self):
        return self._attr_native_value

class PillNextDoseSensor(RestoreSensor):
    def __init__(self, entry):
        med_name = entry.data["medication_name"]
        self._attr_name = f"{med_name} Next Dose"
        self._attr_unique_id = f"{entry.entry_id}_next_dose"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._entry_id = entry.entry_id
        self._tracking_type = entry.data.get("tracking_type")
        self._hours_between_doses = entry.data.get("hours_between_doses", 0)
        self._max_pills = entry.data.get("max_pills_allowed", 0)
        self._time_window = entry.data.get("time_window_hours", 0)
        self._time_of_day = entry.data.get("time_of_day")
        
        self._timestamps = []
        self._attr_extra_state_attributes = {"timestamps": []}
        self._attr_native_value = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_taken_{self._entry_id}", self.pill_taken)
        )
            
        last_state_obj = await self.async_get_last_state()
        if last_state_obj and "timestamps" in last_state_obj.attributes:
            saved_timestamps = last_state_obj.attributes["timestamps"]
            for ts_str in saved_timestamps:
                dt = dt_util.parse_datetime(ts_str)
                if dt:
                    self._timestamps.append(dt)
        self._update_state()

    def pill_taken(self):
        self._timestamps.append(dt_util.now())
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        now = dt_util.now()
        
        if self._tracking_type == "Regular Interval":
            if self._timestamps:
                last_ts = self._timestamps[-1]
                self._attr_native_value = last_ts + timedelta(hours=self._hours_between_doses)
            else:
                self._attr_native_value = now
        elif self._tracking_type == "Time of Day":
            if self._time_of_day:
                try:
                    target_hour, target_minute = map(int, self._time_of_day.split(":"))
                except ValueError:
                    target_hour, target_minute = 8, 0
                
                target_today = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                
                if self._timestamps:
                    last_ts = self._timestamps[-1]
                    # Check if the last_ts is on the same calendar day in local time
                    if last_ts.date() == now.date():
                        self._attr_native_value = target_today + timedelta(days=1)
                    else:
                        self._attr_native_value = target_today
                else:
                    self._attr_native_value = target_today
        elif self._tracking_type == "As Needed":
            cutoff = now - timedelta(hours=self._time_window)
            self._timestamps = [ts for ts in self._timestamps if ts >= cutoff]
            safe_doses = max(0, self._max_pills - len(self._timestamps))
            
            if safe_doses > 0:
                self._attr_native_value = None
            else:
                if self._timestamps:
                    self._attr_native_value = self._timestamps[0] + timedelta(hours=self._time_window)
                else:
                    self._attr_native_value = None
                    
        self._attr_extra_state_attributes = {
            "timestamps": [ts.isoformat() for ts in self._timestamps]
        }

    @property
    def native_value(self):
        return self._attr_native_value
