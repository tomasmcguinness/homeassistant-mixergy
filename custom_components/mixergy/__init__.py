from .const import ATTR_CHARGE, SERVICE_SET_CHARGE, ATTR_TEMPERATURE, SERVICE_SET_TARGET_TEMPERATURE, ATTR_START_DATE, ATTR_END_DATE, SERVICE_SET_HOLIDAY_DATES, SERVICE_CLEAR_HOLIDAY_DATES, SERVICE_SET_DEFAULT_HEAT_SOURCE, ATTR_HEAT_SOURCE
from datetime import timedelta
import logging
import asyncio
from pathlib import Path
import voluptuous as vol
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import LOVELACE_DATA, MODE_STORAGE
from homeassistant import core
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.config_validation import make_entity_service_schema
from homeassistant.helpers.service import verify_domain_control
from .tank import Tank
from typing import Final, final
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

CHARGE_SERVICE_SCHEMA: Final = make_entity_service_schema(
    {vol.Optional("target_percentage"): cv.positive_int}
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema("mixergy")

DOMAIN = "mixergy"
PLATFORMS:list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]
CARD_URL = "/mixergy/mixergy-card.js"
CARD_PATH = Path(__file__).parent / "www" / "mixergy-card.js"

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config):
    _LOGGER.info("Setting up mixergy tank...")

    hass.data[DOMAIN] = {}

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=False),
            StaticPathConfig(
                "/mixergy/translations",
                str(Path(__file__).parent / "translations"),
                cache_headers=False,
            ),
        ]
    )
    await _async_register_lovelace_card(hass)

    return True

async def _async_register_lovelace_card(hass: HomeAssistant) -> None:
    """Register the Mixergy card as a Lovelace resource."""
    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        _LOGGER.warning("Lovelace is unavailable; the Mixergy card was not registered")
        return

    resources = lovelace_data.resources
    if lovelace_data.resource_mode != MODE_STORAGE:
        if not any(
            resource["url"].split("?", maxsplit=1)[0] == CARD_URL
            for resource in resources.async_items()
        ):
            _LOGGER.warning(
                "Lovelace resources are YAML-managed; add %s as a module resource",
                CARD_URL,
            )
        return

    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True

    if not any(
        resource["url"].split("?", maxsplit=1)[0] == CARD_URL
        for resource in resources.async_items()
    ):
        await resources.async_create_item({"res_type": "module", "url": CARD_URL})

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

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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

    async def mixergy_set_holiday_dates(call):

        start_date = call.data[ATTR_START_DATE]
        end_date = call.data[ATTR_END_DATE]

        tasks = [
            tank.set_holiday_dates(start_date, end_date)
            for tank in [d["tank"] for d in hass.data[DOMAIN].values()]
            if isinstance(tank, Tank)
        ]

        results = await asyncio.gather(*tasks)

        # Note that we'll get a "None" value for a successful call
        if None not in results:
            _LOGGER.warning("The request to change the holiday dates of the tank did not succeed")

    async def mixergy_clear_holiday_dates(call):

        tasks = [
            tank.clear_holiday_dates()
            for tank in [d["tank"] for d in hass.data[DOMAIN].values()]
            if isinstance(tank, Tank)
        ]

        results = await asyncio.gather(*tasks)

        # Note that we'll get a "None" value for a successful call
        if None not in results:
            _LOGGER.warning("The request to clear the holiday dates of the tank did not succeed")

    async def mixergy_set_default_heat_source(call):

        heat_source = call.data[ATTR_HEAT_SOURCE]

        tasks = [
            tank.set_default_heat_source(heat_source)
            for tank in [d["tank"] for d in hass.data[DOMAIN].values()]
            if isinstance(tank, Tank)
        ]

        results = await asyncio.gather(*tasks)

        # Note that we'll get a "None" value for a successful call
        if None not in results:
            _LOGGER.warning("The request to set the default heat source of the tank did not succeed")

    if not hass.services.has_service(DOMAIN, SERVICE_SET_CHARGE):
        # Register a local handler for scene activation
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_CHARGE,
            verify_domain_control(DOMAIN)(mixergy_set_charge),
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
            verify_domain_control(DOMAIN)(mixergy_set_target_temperature),
            schema=vol.Schema(
                {
                    vol.Required(ATTR_TEMPERATURE): cv.positive_int
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_HOLIDAY_DATES):
        # Register a local handler for scene activation
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_HOLIDAY_DATES,
            verify_domain_control(DOMAIN)(mixergy_set_holiday_dates),
            schema=vol.Schema(
                {
                    vol.Required(ATTR_START_DATE): cv.datetime,
                    vol.Required(ATTR_END_DATE): cv.datetime
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_HOLIDAY_DATES):
        # Register a local handler for scene activation
        hass.services.async_register(
            DOMAIN,
            SERVICE_CLEAR_HOLIDAY_DATES,
            verify_domain_control(DOMAIN)(mixergy_clear_holiday_dates),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_DEFAULT_HEAT_SOURCE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_DEFAULT_HEAT_SOURCE,
            verify_domain_control(DOMAIN)(mixergy_set_default_heat_source),
            schema=vol.Schema(
                {
                    vol.Required(ATTR_HEAT_SOURCE): cv.string
                }
            ),
        )
