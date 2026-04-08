from datetime import timedelta
from homeassistant.components.sensor import RestoreSensor, SensorDeviceClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.util.dt as dt_util
from .const import DOMAIN  

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    med_name = entry.data["medication_name"]
    entities = [PillTotalSensor(med_name, entry.entry_id)]
    entities.append(PillSafeDosesSensor(entry))
    entities.append(PillNextDoseSensor(entry))
    entities.append(PillAvgDosesSensor(entry, 7, "Avg Daily Doses (7 Days)"))
    entities.append(PillAvgDosesSensor(entry, 30, "Avg Daily Doses (30 Days)"))
    entities.append(PillAvgDosesSensor(entry, 365, "Avg Daily Doses (Yearly)"))
    async_add_entities(entities)  

class PillTotalSensor(RestoreSensor):
    def __init__(self, name, entry_id):
        self._med_name = name
        self._attr_name = f"{name} Total Doses"
        self._attr_unique_id = f"{entry_id}_total"
        self._attr_icon = "mdi:chart-line"
        self._entry_id = entry_id
        self._state = 0  

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
            async_dispatcher_connect(self.hass, f"pill_taken_{self._entry_id}", self.increment)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_reset_{self._entry_id}", self.reset_data)
        )
        last_state = await self.async_get_last_sensor_data()
        if last_state and last_state.native_value is not None:
            self._state = int(last_state.native_value)  

    @property
    def native_value(self):
        return self._state  

    @callback
    def increment(self, *args, **kwargs):
        self._state += 1
        self.async_write_ha_state()

    @callback
    def reset_data(self, *args, **kwargs):
        self._state = 0
        self.async_write_ha_state()  


class PillSafeDosesSensor(RestoreSensor):
    def __init__(self, entry):
        med_name = entry.data["medication_name"]
        self._med_name = med_name
        self._attr_name = f"{med_name} Safe Doses"
        self._attr_unique_id = f"{entry.entry_id}_safe_doses"
        self._attr_icon = "mdi:pill"
        self._entry_id = entry.entry_id
        self._tracking_type = entry.data.get("tracking_type")
        self._max_pills = entry.options.get("safe_doses", entry.data.get("safe_doses", entry.data.get("max_pills_allowed", 1)))
        self._time_window = entry.options.get("time_window_hours", entry.data.get("time_window_hours", 0))
        self._time_of_day = entry.options.get("time_of_day", entry.data.get("time_of_day"))
        self._timestamps = []
        self._attr_extra_state_attributes = {"timestamps": []}
        self._attr_native_value = None  

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_taken_{self._entry_id}", self.pill_taken)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_reset_{self._entry_id}", self.reset_data)
        )
        
        # Track time passage to prune array and update state every minute
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._on_interval, timedelta(minutes=1)
            )
        )

        last_state_obj = await self.async_get_last_state()
        if last_state_obj and "timestamps" in last_state_obj.attributes:
            saved_timestamps = last_state_obj.attributes["timestamps"]
            for ts_str in saved_timestamps:
                dt = dt_util.parse_datetime(ts_str)
                if dt:
                    self._timestamps.append(dt)
            self._update_state()  

    @callback
    def _on_interval(self, now):
        """Callback to execute mathematical update each minute."""
        self._update_state()
        self.async_write_ha_state()

    @callback
    def pill_taken(self, *args, **kwargs):
        self._timestamps.append(dt_util.now())
        self._update_state()
        self.async_write_ha_state()

    @callback
    def reset_data(self, *args, **kwargs):
        self._timestamps = []
        self._update_state()
        self.async_write_ha_state()  

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._med_name,
            manufacturer="Pill Logger",
        )  

    def _update_state(self):
        now = dt_util.now()  
        if self._tracking_type == "As Needed":
            cutoff = now - timedelta(hours=self._time_window)
            self._timestamps = [ts for ts in self._timestamps if ts >= cutoff]
            self._attr_native_value = max(0, self._max_pills - len(self._timestamps))  
        elif self._tracking_type == "Regular Interval":
            # Set native_value to 0 if the time since the last pill is less than hours_between_doses
            entry = self.hass.config_entries.async_get_entry(self._entry_id)
            hours_between = entry.options.get("hours_between_doses", entry.data.get("hours_between_doses", 0))
            if self._timestamps:
                last_ts = self._timestamps[-1]
                if now - last_ts < timedelta(hours=hours_between):
                    self._attr_native_value = 0
                else:
                    self._attr_native_value = self._max_pills
            else:
                self._attr_native_value = self._max_pills
        elif self._tracking_type == "Time of Day":
            if self._timestamps:
                last_ts = self._timestamps[-1]
                
                if self._time_of_day:
                    try:
                        target_hour, target_minute = map(int, self._time_of_day.split(":"))
                    except ValueError:
                        target_hour, target_minute = 8, 0  
                    
                    # The safe dose becomes available on the day after the last pill was taken, at the target time.
                    # This ensures that Safe Doses is 0 until the expected next dose time passes.
                    release_time = last_ts.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0) + timedelta(days=1)
                        
                    if now >= release_time:
                        self._attr_native_value = self._max_pills
                    else:
                        self._attr_native_value = 0
                else:
                    if last_ts.date() == now.date():
                        self._attr_native_value = 0
                    else:
                        self._attr_native_value = self._max_pills
            else:
                self._attr_native_value = self._max_pills
            
        self._attr_extra_state_attributes = {
            "timestamps": [ts.isoformat() for ts in self._timestamps]
        }  

    @property
    def native_value(self):
        return self._attr_native_value  


class PillNextDoseSensor(RestoreSensor):
    def __init__(self, entry):
        med_name = entry.data["medication_name"]
        self._med_name = med_name
        self._attr_name = f"{med_name} Next Dose"
        self._attr_unique_id = f"{entry.entry_id}_next_dose"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._entry_id = entry.entry_id
        self._tracking_type = entry.data.get("tracking_type")
        self._hours_between_doses = entry.options.get("hours_between_doses", entry.data.get("hours_between_doses", 0))
        self._max_pills = entry.options.get("safe_doses", entry.data.get("safe_doses", entry.data.get("max_pills_allowed", 1)))
        self._time_window = entry.options.get("time_window_hours", entry.data.get("time_window_hours", 0))
        self._time_of_day = entry.options.get("time_of_day", entry.data.get("time_of_day"))  
        self._timestamps = []
        self._attr_extra_state_attributes = {"timestamps": []}
        self._attr_native_value = None  

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_taken_{self._entry_id}", self.pill_taken)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_reset_{self._entry_id}", self.reset_data)
        )  

        # Track time passage to recalculate the next dose mathematically every minute
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._on_interval, timedelta(minutes=1)
            )
        )

        last_state_obj = await self.async_get_last_state()
        if last_state_obj and "timestamps" in last_state_obj.attributes:
            saved_timestamps = last_state_obj.attributes["timestamps"]
            for ts_str in saved_timestamps:
                dt = dt_util.parse_datetime(ts_str)
                if dt:
                    self._timestamps.append(dt)
            self._update_state()  

    @callback
    def _on_interval(self, now):
        """Callback to execute mathematical update each minute."""
        self._update_state()
        self.async_write_ha_state()

    @callback
    def pill_taken(self, *args, **kwargs):
        self._timestamps.append(dt_util.now())
        self._update_state()
        self.async_write_ha_state()

    @callback
    def reset_data(self, *args, **kwargs):
        self._timestamps = []
        self._update_state()
        self.async_write_ha_state()  

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._med_name,
            manufacturer="Pill Logger",
        )  

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


class PillAvgDosesSensor(RestoreSensor):
    def __init__(self, entry, window_days, sensor_name):
        med_name = entry.data["medication_name"]
        self._med_name = med_name
        self._window_days_target = window_days
        self._attr_name = f"{med_name} {sensor_name}"
        self._attr_unique_id = f"{entry.entry_id}_avg_doses_{window_days}"
        self._attr_icon = "mdi:chart-bell-curve"
        self._entry_id = entry.entry_id
        self._timestamps = []
        self._history_start_date = None
        self._attr_extra_state_attributes = {"timestamps": [], "history_start_date": None}
        self._attr_native_value = 0.0

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_taken_{self._entry_id}", self.pill_taken)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"pill_reset_{self._entry_id}", self.reset_data)
        )

        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._on_interval, timedelta(hours=1)
            )
        )

        last_state_obj = await self.async_get_last_state()
        if last_state_obj:
            if "timestamps" in last_state_obj.attributes:
                saved_timestamps = last_state_obj.attributes["timestamps"]
                for ts_str in saved_timestamps:
                    dt = dt_util.parse_datetime(ts_str)
                    if dt:
                        self._timestamps.append(dt)
            if "history_start_date" in last_state_obj.attributes and last_state_obj.attributes["history_start_date"]:
                self._history_start_date = dt_util.parse_datetime(last_state_obj.attributes["history_start_date"])

        if self._history_start_date is None:
            self._history_start_date = dt_util.now()

        self._update_state()

    @callback
    def _on_interval(self, now):
        self._update_state()
        self.async_write_ha_state()

    @callback
    def pill_taken(self, *args, **kwargs):
        self._timestamps.append(dt_util.now())
        self._update_state()
        self.async_write_ha_state()

    @callback
    def reset_data(self, *args, **kwargs):
        self._timestamps = []
        self._history_start_date = dt_util.now()
        self._update_state()
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._med_name,
            manufacturer="Pill Logger",
        )

    def _update_state(self):
        now = dt_util.now()
        if not self._history_start_date:
            self._history_start_date = now

        days_since_start = (now - self._history_start_date).total_seconds() / 86400.0
        days_since_start = max(1.0, days_since_start)

        actual_window_days = min(days_since_start, float(self._window_days_target))
        cutoff = now - timedelta(days=actual_window_days)

        self._timestamps = [ts for ts in self._timestamps if ts >= cutoff]

        if actual_window_days > 0:
            avg = len(self._timestamps) / actual_window_days
            self._attr_native_value = round(avg, 2)
        else:
            self._attr_native_value = 0.0

        self._attr_extra_state_attributes = {
            "timestamps": [ts.isoformat() for ts in self._timestamps],
            "history_start_date": self._history_start_date.isoformat() if self._history_start_date else None
        }

    @property
    def native_value(self):
        return self._attr_native_value
