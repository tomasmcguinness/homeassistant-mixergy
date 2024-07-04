from .const import DOMAIN
from .tank import Tank
from homeassistant.helpers.entity import Entity

class MixergyEntityBase(Entity):

    should_poll = False

    def __init__(self, tank:Tank):
        super().__init__()
        self._tank = tank

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._tank.serial_number)},
            "manufacturer": "Mixergy Ltd",
            "name": "Mixergy Tank",
            "suggested_area": "garage",
            "model": self._tank.model_code,
            "sw_version": self._tank.firmware_version
        }

    @property
    def available(self) -> bool:
        return self._tank.online

    async def async_added_to_hass(self):
        self._tank.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._tank.remove_callback(self.async_write_ha_state)
