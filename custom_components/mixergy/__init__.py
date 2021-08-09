import logging
import asyncio
from homeassistant.helpers import aiohttp_client
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from . import tank

DOMAIN = "mixergy"
PLATFORMS = ["number","sensor"]
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    _LOGGER.info("Setting up mixergy tank...")
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry:ConfigEntry) -> bool:

    hass.data[DOMAIN][entry.entry_id] = tank.Tank(hass, entry.data["username"],entry.data["password"],entry.data["serial_number"])

    for component in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, component))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
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