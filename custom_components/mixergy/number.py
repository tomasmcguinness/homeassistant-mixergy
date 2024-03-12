import logging
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.components.number import NumberEntity, NumberDeviceClass
from .const import DOMAIN
from .tank import Tank
from .mixergy_entity import MixergyEntityBase

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.info("Setting up entry based on user config")

    entry = hass.data[DOMAIN][config_entry.entry_id]
    tank = entry["tank"]
    coordinator = entry["coordinator"]

    new_entities = []

    new_entities.append(TargetTemperatureSensor(coordinator, tank))
    new_entities.append(TargetChargeSensor(coordinator, tank))
    new_entities.append(CleansingTemperatureSensor(coordinator, tank))
    new_entities.append(PVCutInThreshold(coordinator, tank))
    new_entities.append(PVChargeLimitSensor(coordinator, tank))
    new_entities.append(PVTargetCurrent(coordinator, tank))
    new_entities.append(PVOverTemperature(coordinator, tank))

    async_add_entities(new_entities)

class NumberEntityBase(MixergyEntityBase, NumberEntity):

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

class TargetTemperatureSensor(NumberEntityBase):

    native_max_value = 55
    native_min_value = 45
    native_step = 1
    device_class = NumberDeviceClass.TEMPERATURE
    native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, tank:Tank):
        super().__init__( coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.serial_number}_target_temperature"

    @property
    def state(self):
        return self._tank.target_temperature

    async def async_set_native_value(self, value: float):
        await self._tank.set_target_temperature(int(value))

    @property
    def name(self):
        return f"Target Temperature"

class TargetChargeSensor(NumberEntityBase):

    native_max_value = 100
    native_min_value = 0
    native_step = 1
    native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.serial_number}_target_charge"

    @property
    def state(self):
        return self._tank.target_charge

    @property
    def icon(self):
        return "hass:water-percent"

    async def async_set_native_value(self, value: float):
        await self._tank.set_target_charge(int(value))

    @property
    def name(self):
        return f"Target Charge"

class CleansingTemperatureSensor(NumberEntityBase):

    native_max_value = 55
    native_min_value = 51
    native_step = 1
    device_class = NumberDeviceClass.TEMPERATURE
    native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, tank:Tank):
        super().__init__( coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.serial_number}_cleansing_temperature"

    @property
    def state(self):
        return self._tank.cleansing_temperature

    async def async_set_native_value(self, value: float):
        await self._tank.set_cleansing_temperature(int(value))

    @property
    def name(self):
        return f"Cleansing Temperature"

class PVCutInThreshold(NumberEntityBase):

    native_max_value = 500
    native_min_value = 0
    native_step = 50

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_pv_cut_in_threshold"

    @property
    def state(self):
        return self._tank.pv_cut_in_threshold

    @property
    def available(self):
        return super().available and self._tank.has_pv_diverter

    async def async_set_native_value(self, value: float):
        await self._tank.set_pv_cut_in_threshold(int(value))

    @property
    def icon(self):
        return "mdi:lightning-bolt"

    @property
    def name(self):
        return f"PV Cut In Threshold"

class PVChargeLimitSensor(NumberEntityBase):

    native_max_value = 100
    native_min_value = 0
    native_step = 10

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_pv_charge_limit"

    @property
    def state(self):
        return self._tank.pv_charge_limit

    @property
    def available(self):
        return super().available and self._tank.has_pv_diverter

    async def async_set_native_value(self, value: float):
        await self._tank.set_pv_charge_limit(int(value))

    @property
    def icon(self):
        return "mdi:lightning-bolt"

    @property
    def name(self):
        return f"PV Charge Limit"

class PVTargetCurrent(NumberEntityBase):

    native_max_value = 0
    native_min_value = -1
    native_step = 0.1

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_pv_target_current"

    @property
    def state(self):
        return self._tank.pv_target_current

    @property
    def available(self):
        return super().available and self._tank.has_pv_diverter

    async def async_set_native_value(self, value: float):
        await self._tank.set_pv_target_current(value)

    @property
    def icon(self):
        return "mdi:lightning-bolt"

    @property
    def name(self):
        return f"PV Target Current"

class PVOverTemperature(NumberEntityBase):

    native_max_value = 60
    native_min_value = 45
    native_step = 1

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_pv_over_temperature"

    @property
    def state(self):
        return self._tank.pv_over_temperature

    @property
    def available(self):
        return super().available and self._tank.has_pv_diverter

    async def async_set_native_value(self, value: float):
        await self._tank.set_pv_over_temperature(int(value))

    @property
    def icon(self):
        return "mdi:lightning-bolt"

    @property
    def name(self):
        return f"PV Target Temperature"
