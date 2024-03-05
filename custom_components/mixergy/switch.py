import logging
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
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

    new_entities.append(PVDivertSwitch(coordinator, tank))
    
    async_add_entities(new_entities)

class SwitchEntityBase(MixergyEntityBase, SwitchEntity):

    device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

class PVDivertSwitch(SwitchEntityBase):

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator, tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_pv_divert_enabled"

    @property
    def name(self):
        return f"PV Divert Enabled"
    
    @property
    def available(self):
        return super().available and self._tank.has_pv_diverter

    @property
    def is_on(self):
        return self._tank.divert_exported_enabled

    async def async_turn_on(self, **kwargs):
        await self._tank.set_divert_exported_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self._tank.set_divert_exported_enabled(False)
