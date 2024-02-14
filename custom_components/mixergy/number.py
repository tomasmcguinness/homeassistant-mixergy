import logging
from homeassistant.components.number import NumberEntity
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

    new_entities.append(PVChargeLimitSensor(coordinator, tank))

    async_add_entities(new_entities)

class NumberEntityBase(MixergyEntityBase, NumberEntity):

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

class PVChargeLimitSensor(NumberEntityBase):

    native_max_value = 100
    native_min_value = 0
    native_step = 10

    def __init__(self, coordinator, tank:Tank):
        super().__init__( coordinator, tank)

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
