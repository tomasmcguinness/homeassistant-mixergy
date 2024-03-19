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

    new_entities = []

    new_entities.append(DSRSwitch(tank))
    new_entities.append(FrostProtectionSwitch(tank))
    new_entities.append(DistributedComputingSwitch(tank))
    new_entities.append(PVDivertSwitch(tank))

    async_add_entities(new_entities)

class SwitchEntityBase(MixergyEntityBase, SwitchEntity):

    device_class = SwitchDeviceClass.SWITCH

    def __init__(self, tank:Tank):
        super().__init__(tank)

class DSRSwitch(SwitchEntityBase):

    def __init__(self, tank:Tank):
        super().__init__(tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_dsr_enabled"

    @property
    def name(self):
        return f"Grid Assistance Enabled"

    @property
    def is_on(self):
        return self._tank.dsr_enabled

    async def async_turn_on(self, **kwargs):
        await self._tank.set_dsr_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self._tank.set_dsr_enabled(False)

class FrostProtectionSwitch(SwitchEntityBase):

    def __init__(self, tank:Tank):
        super().__init__(tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_frost_protection_enabled"

    @property
    def name(self):
        return f"Frost Protection Enabled"

    @property
    def is_on(self):
        return self._tank.frost_protection_enabled

    async def async_turn_on(self, **kwargs):
        await self._tank.set_frost_protection_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self._tank.set_frost_protection_enabled(False)

class DistributedComputingSwitch(SwitchEntityBase):

    def __init__(self, tank:Tank):
        super().__init__(tank)

    @property
    def unique_id(self):
        return f"mixergy_{self._tank.tank_id}_distributed_computng_enabled"

    @property
    def name(self):
        return f"Medical Research Donation Enabled"

    @property
    def is_on(self):
        return self._tank.distributed_computing_enabled

    async def async_turn_on(self, **kwargs):
        await self._tank.set_distributed_computing_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self._tank.set_distributed_computing_enabled(False)

class PVDivertSwitch(SwitchEntityBase):

    def __init__(self, tank:Tank):
        super().__init__(tank)

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
