from .const import ATTR_CHARGE, SERVICE_SET_CHARGE, ATTR_TEMPERATURE, SERVICE_SET_TARGET_TEMPERATURE
from datetime import timedelta
import logging
import asyncio
import voluptuous as vol
from homeassistant import core
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.config_validation import make_entity_service_schema
from homeassistant.helpers.service import verify_domain_control
from .tank import Tank
from typing import Any, Final, final
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

CHARGE_SERVICE_SCHEMA: Final = make_entity_service_schema(
    {vol.Optional("target_percentage"): cv.positive_int}
)

DOMAIN = "mixergy"
PLATFORMS = [
    "sensor",
    "switch",
]
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config):
    _LOGGER.info("Setting up mixergy tank...")

    hass.data[DOMAIN] = {}

    hass.services.async_register(DOMAIN, 'demo', my_service)

    return True

async def my_service(call: ServiceCall):
    _LOGGER.info()

async def async_setup_entry(hass: HomeAssistant, entry:ConfigEntry) -> bool:

    """Set up a tank from a config entry."""

    tank = Tank(hass, entry.data[CONF_USERNAME],entry.data[CONF_PASSWORD],entry.data["serial_number"])

    async def async_update_data():
        _LOGGER.info("Fetching data from Mixergy...")
        await tank.fetch_data()

    # Create a coordinator to fetch data from the Mixergy API.
    coordinator = DataUpdateCoordinator(hass, _LOGGER, name="Mixergy", update_method = async_update_data, update_interval = timedelta(seconds=30))
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "tank": tank,
        "coordinator": coordinator,
    }

    _register_services(hass)

    for component in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, component))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

@core.callback
def _register_services(hass):
    """Register Mixergy services."""

    async def mixergy_set_charge(call):

        charge = call.data[ATTR_CHARGE]

        tasks = [
            tank.set_target_charge(charge)
            for tank in [d["tank"] for d in hass.data[DOMAIN].values()]
            if isinstance(tank, Tank)
        ]

        results = await asyncio.gather(*tasks)

        # Note that we'll get a "None" value for a successful call
        if None not in results:
            _LOGGER.warning("The request to charge the tank did not succeed")

    async def mixergy_set_target_temperature(call):

        temperature = call.data[ATTR_TEMPERATURE]

        tasks = [
            tank.set_target_temperature(temperature)
            for tank in [d["tank"] for d in hass.data[DOMAIN].values()]
            if isinstance(tank, Tank)
        ]

        results = await asyncio.gather(*tasks)

        # Note that we'll get a "None" value for a successful call
        if None not in results:
            _LOGGER.warning("The request to change the target temperature of the tank did not succeed")

    if not hass.services.has_service(DOMAIN, SERVICE_SET_CHARGE):
        # Register a local handler for scene activation
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_CHARGE,
            verify_domain_control(hass, DOMAIN)(mixergy_set_charge),
            schema=vol.Schema(
                {
                    vol.Required(ATTR_CHARGE): cv.positive_int
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_TARGET_TEMPERATURE):
        # Register a local handler for scene activation
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_TARGET_TEMPERATURE,
            verify_domain_control(hass, DOMAIN)(mixergy_set_target_temperature),
            schema=vol.Schema(
                {
                    vol.Required(ATTR_TEMPERATURE): cv.positive_int
                }
            ),
        )
