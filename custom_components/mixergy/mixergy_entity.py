from .const import DOMAIN
from .tank import Tank
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class MixergyEntityBase(CoordinatorEntity):

    should_poll = True

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator)        
        self._tank = tank

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._tank.serial_number)},
            "manufacturer": "Mixergy Ltd",
            "name": "Mixergy Tank",
            "suggested_area": "garage",
            "model": self._tank.modelCode,
            "sw_version": self._tank.firmwareVersion
        }

    @property
    def available(self) -> bool:
        return self._tank.online

    async def async_added_to_hass(self):
        self._tank.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._tank.remove_callback(self.async_write_ha_state)
