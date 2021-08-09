import logging
import random
from datetime import timedelta
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS
from homeassistant.components.sensor import Entity
from homeassistant.components.sensor import DEVICE_CLASS_TEMPERATURE
from .const import DOMAIN
from .tank import Tank
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.info("Setting up entry based on user config")

    tank = hass.data[DOMAIN][config_entry.entry_id]

    async def async_update_data():
        _LOGGER.info("Fetching data from Mixergy...")
        await tank.fetch_data()

    coordinator = DataUpdateCoordinator(hass, _LOGGER, name="sensor", update_method = async_update_data, update_interval = timedelta(seconds=30))

    await coordinator.async_config_entry_first_refresh()

    new_entities = []

    new_entities.append(HotWaterTemperatureSensor(coordinator, tank))
    new_entities.append(ColdestWaterTemperatureSensor(coordinator, tank))
    new_entities.append(ChargeSensor(coordinator,tank))

    async_add_entities(new_entities)

class ChargeSensor(CoordinatorEntity,Entity):
    should_poll = True

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator)
        self._tank = tank

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._tank.serial_number)},
            "manufacturer":"Mixergy Ltd",
            "name":"Mixergy Tank",
            "suggested_area":"garage",
            "model":self._tank.modelCode,
            "sw_version":self._tank.firmwareVersion
        }

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_charge"

    @property
    def unit_of_measurement(self):
        return PERCENTAGE

    @property
    def state(self):
        return self._tank.charge

    @property
    def name(self):
        return f"Current Charge"

class SensorBase(CoordinatorEntity,Entity):

    should_poll = True

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator)
        self._tank = tank

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._tank.serial_number)},
            "manufacturer":"Mixergy Ltd",
            "name":"Mixergy Tank",
            "suggested_area":"garage",
            "model":self._tank.modelCode,
            "sw_version":self._tank.firmwareVersion
        }

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        return self._tank.online and self._tank.online

    async def async_added_to_hass(self):
        # Sensors should also register callbacks to HA when their state changes
        self._tank.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._tank.remove_callback(self.async_write_ha_state)


class HotWaterTemperatureSensor(SensorBase):

    # The class of this device. Note the value should come from the homeassistant.const
    # module. More information on the available devices classes can be seen here:
    # https://developers.home-assistant.io/docs/core/entity/sensor
    device_class = DEVICE_CLASS_TEMPERATURE

    def __init__(self, coordinator, tank):
        """Initialize the sensor."""
        super().__init__( coordinator, tank)
        self._state = random.randint(0, 100)

    # As per the sensor, this must be a unique value within this domain. This is done
    # by using the device ID, and appending "_battery"
    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"mixergy_{self._tank.tank_id}_hot_water_temperature"

    # The value of this sensor. As this is a DEVICE_CLASS_BATTERY, this value must be
    # the battery level as a percentage (between 0 and 100)
    @property
    def state(self):
        return self._tank.hot_water_temperature

    # The unit of measurement for this entity. As it's a DEVICE_CLASS_BATTERY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

    # The same of this entity, as displayed in the entity UI.
    @property
    def name(self):
        return f"Hot Water Temperature"


class ColdestWaterTemperatureSensor(SensorBase):

    # The class of this device. Note the value should come from the homeassistant.const
    # module. More information on the available devices classes can be seen here:
    # https://developers.home-assistant.io/docs/core/entity/sensor
    device_class = DEVICE_CLASS_TEMPERATURE

    def __init__(self, coordinator, tank):
        super().__init__(coordinator, tank)
        self._state = random.randint(0, 100)

    # As per the sensor, this must be a unique value within this domain. This is done
    # by using the device ID, and appending "_battery"
    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_coldest_water_temperature"

    # The value of this sensor. As this is a DEVICE_CLASS_BATTERY, this value must be
    # the battery level as a percentage (between 0 and 100)
    @property
    def state(self):
        return self._tank.coldest_water_temperature

    # The unit of measurement for this entity. As it's a DEVICE_CLASS_BATTERY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

    # The same of this entity, as displayed in the entity UI.
    @property
    def name(self):
        return f"Coldest Water Temperature"

