import logging
from datetime import timedelta
from homeassistant.const import DEVICE_CLASS_ENERGY, DEVICE_CLASS_POWER, PERCENTAGE, TEMP_CELSIUS, STATE_OFF, POWER_WATT
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.components.binary_sensor import BinarySensorEntity, DEVICE_CLASS_HEAT
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

    # Create a coordinator to fetch data from the Mixergy API.
    coordinator = DataUpdateCoordinator(hass, _LOGGER, name="sensor", update_method = async_update_data, update_interval = timedelta(seconds=30))

    await coordinator.async_config_entry_first_refresh()

    new_entities = []

    new_entities.append(HotWaterTemperatureSensor(coordinator, tank))
    new_entities.append(ColdestWaterTemperatureSensor(coordinator, tank))
    new_entities.append(ChargeSensor(coordinator, tank))
    new_entities.append(ElectricHeatSensor(coordinator, tank))
    new_entities.append(IndirectHeatSensor(coordinator, tank))
    new_entities.append(LowChargeSensor(coordinator, tank))
    new_entities.append(NoChargeSensor(coordinator, tank))
    new_entities.append(PowerSensor(coordinator, tank))
    new_entities.append(EnergySensor(coordinator))

    async_add_entities(new_entities)

class SensorBase(CoordinatorEntity,SensorEntity):

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
    def available(self) -> bool:
        return self._tank.online

    async def async_added_to_hass(self):
        self._tank.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._tank.remove_callback(self.async_write_ha_state)

class BinarySensorBase(CoordinatorEntity,BinarySensorEntity):

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
    def available(self) -> bool:
        return self._tank.online

    async def async_added_to_hass(self):
        self._tank.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._tank.remove_callback(self.async_write_ha_state)

class ChargeSensor(SensorBase):

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.serial_number}_charge"

    @property
    def unit_of_measurement(self):
        return PERCENTAGE

    @property
    def state(self):
        return self._tank.charge

    @property
    def icon(self):
        return "hass:water-percent"

    @property
    def name(self):
          return f"Current Charge"

class HotWaterTemperatureSensor(SensorBase):

    device_class = DEVICE_CLASS_TEMPERATURE

    def __init__(self, coordinator, tank:Tank):
        super().__init__( coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.serial_number}_hot_water_temperature"

    @property
    def state(self):
        return self._tank.hot_water_temperature

    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

    @property
    def name(self):
        return f"Hot Water Temperature"


class ColdestWaterTemperatureSensor(SensorBase):

    device_class = DEVICE_CLASS_TEMPERATURE

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.serial_number}_coldest_water_temperature"

    @property
    def state(self):
        return self._tank.coldest_water_temperature

    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

    @property
    def name(self):
        return f"Coldest Water Temperature"

class IndirectHeatSensor(BinarySensorBase):

    device_class = DEVICE_CLASS_HEAT

    def __init__(self, coordinator, tank:Tank):
        super().__init__( coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.serial_number}_indirect_heat"

    @property
    def is_on(self):
        return self._tank.indirect_heat_source

    @property
    def icon(self):
        return "mdi:fire"

    @property
    def name(self):
        return f"Indirect Heat"

class ElectricHeatSensor(BinarySensorBase):

    device_class = DEVICE_CLASS_ENERGY

    def __init__(self, coordinator, tank:Tank):
        super().__init__( coordinator, tank)
        self._state = STATE_OFF

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_electic_heat"

    @property
    def is_on(self):
        return self._tank.electic_heat_source

    @property
    def name(self):
        return f"Electric Heat"

class NoChargeSensor(BinarySensorBase):

    def __init__(self, coordinator, tank:Tank):
        super().__init__( coordinator, tank)
        self._state = STATE_OFF

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_no_charge"

    @property
    def is_on(self):
        return self._tank.charge < 0.5

    @property
    def icon(self):
        return "hass:water-remove-outline"

    @property
    def name(self):
        return f"No Hot Water"

class LowChargeSensor(BinarySensorBase):

    def __init__(self, coordinator, tank:Tank):
        super().__init__( coordinator, tank)
        self._state = STATE_OFF

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_low_charge"

    @property
    def is_on(self):
        return self._tank.charge < 5

    @property
    def icon(self):
        return "hass:water-percent-alert"

    @property
    def name(self):
        return f"Low Hot Water"

class PowerSensor(SensorBase):

    device_class = DEVICE_CLASS_POWER
    state_class = "measurement"

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator,tank)
        self._state = 0

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_power"

    @property
    def state(self):
        return 3300 if self._tank.electic_heat_source else 0

    @property
    def unit_of_measurement(self):
        return POWER_WATT;

    @property
    def name(self):
        return f"Mixergy Electric Heat Power"

class EnergySensor(IntegrationSensor):

    def __init__(self, tank:Tank):
        super().__init__(
            name="Mixergy Electric Heat Energy",
            source_entity="sensor.mixergy_electric_heat_power",
            round_digits=2,
            unit_prefix="k",
            unit_time="h",
            integration_method="left",
            unique_id=f"mixergy_{tank.tank_id}_energy"
        )

    @property
    def icon(self):
        return "mdi:lightning-bolt"