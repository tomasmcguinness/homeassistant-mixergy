import logging
import asyncio
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from . import tank

DOMAIN = "mixergy"
PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    _LOGGER.info("Setting up mixergy tank...")
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry:ConfigEntry) -> bool:

    hass.data[DOMAIN][entry.entry_id] = tank.Tank(hass, entry.data[CONF_USERNAME],entry.data[CONF_PASSWORD],entry.data["serial_number"])

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