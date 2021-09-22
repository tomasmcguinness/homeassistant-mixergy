from .const import ATTR_PERCENTAGE, SERVICE_SET_CHARGE
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

CHARGE_SERVICE_SCHEMA: Final = make_entity_service_schema(
    {vol.Optional("target_percentage"): cv.positive_int}
)

DOMAIN = "mixergy"
PLATFORMS = ["sensor"]
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

    hass.data[DOMAIN][entry.entry_id] = tank

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

    async def mixergy_set_charge(call, skip_reload=True):

        tasks = [
            tank.set_target_charge(call.data)
            for tank in hass.data[DOMAIN].values()
            if isinstance(tank, Tank)
        ]
        results = await asyncio.gather(*tasks)

    if not hass.services.has_service(DOMAIN, SERVICE_SET_CHARGE):
        # Register a local handler for scene activation
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_CHARGE,
            verify_domain_control(hass, DOMAIN)(mixergy_set_charge),
            schema=vol.Schema(
                {
                    vol.Required(ATTR_PERCENTAGE): cv.positive_int
                }
            ),
        )