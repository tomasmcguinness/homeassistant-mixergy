import logging
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from .const import DOMAIN
from .tank import Tank
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.info("Setting up entry based on user config")

    entry = hass.data[DOMAIN][config_entry.entry_id]
    tank = entry["tank"]
    coordinator = entry["coordinator"]

    new_entities = []

    new_entities.append(PVDivertSwitch(coordinator, tank))
    
    async_add_entities(new_entities)

class SwitchEntityBase(CoordinatorEntity, SwitchEntity):

    should_poll = True
    device_class = SwitchDeviceClass.SWITCH

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
        return self._tank.online and self._tank.has_divert_exported_enabled

    @property
    def is_on(self):
        return self._tank.divert_exported_enabled

    async def async_turn_on(self, **kwargs):
        await self._tank.set_divert_exported_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self._tank.set_divert_exported_enabled(False)
