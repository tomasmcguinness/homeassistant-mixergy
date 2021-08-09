import logging
from .const import DOMAIN
from .tank import Tank
from datetime import timedelta
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.info("Setting up entry based on user config")

    #tank = hass.data[DOMAIN][config_entry.entry_id]

    # async def async_update_data():
    #     _LOGGER.info("Fetching data from Mixergy...")
    #     await tank.fetch_data()

    # coordinator = DataUpdateCoordinator(hass, _LOGGER, name="sensor", update_method = async_update_data, update_interval = timedelta(seconds=30))

    # await coordinator.async_config_entry_first_refresh()

    # new_entities = []

    # new_entities.append(ChargeNumber(coordinator, tank))

    # async_add_entities(new_entities)

class ChargeNumber(CoordinatorEntity,NumberEntity):

    should_poll = False

    def __init__(self, coordinator, tank:Tank):
        super().__init__(coordinator)
        self._tank = tank

    @property
    def value(self) -> float:
        return 10.0