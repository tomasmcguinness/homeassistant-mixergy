import logging
import asyncio
import json
from datetime import datetime
from typing import Optional
from homeassistant.helpers import aiohttp_client
from .const import ATTR_CHARGE

_LOGGER = logging.getLogger(__name__)

ROOT_ENDPOINT = "https://www.mixergy.io/api/v2"

class TankUrls:
    def __init__(self, account_url):
        self.account_url = account_url

class Tank:

    manufacturer = "Mixergy Ltd"

    def __init__(self, hass, username, password, serial_number):
        self._id = serial_number.lower()
        self.username = username
        self.password = password
        self.serial_number = serial_number.upper()
        self._hass = hass
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._hot_water_temperature = -1
        self._coldest_water_temperature = -1
        self._charge = -1
        self._target_charge = 0
        self._indirect_heat_source = False
        self._electric_heat_source = False
        self._heatpump_heat_source = False
        self._hasFetched = False
        self._token = ""
        self._latest_measurement_url = ""
        self.model = ""
        self.firmware_version = "0.0.0"
        self._target_temperature = -1
        self._dsr_enabled = False
        self._frost_protection_enabled = False
        self._distributed_computing_enabled = False
        self._cleansing_temperature = 0
        self._in_holiday_mode = False
        self._pv_power = 0
        self._clamp_power = 0
        self._has_pv_diverter = False
        self._divert_exported_enabled = False
        self._pv_cut_in_threshold = 0
        self._pv_charge_limit = 0
        self._pv_target_current = 0
        self._pv_over_temperature = 0
        self._schedule = None

    @property
    def tank_id(self):
        return self._id

    async def test_authentication(self):
        return await self.authenticate()

    async def test_connection(self):
        return await self.fetch_tank_information()
    
    async def set_target_charge(self, charge):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._control_url, headers=headers, json={'charge': charge }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set the desired charge failed with status %i", self._control_url, resp.status)
                return

            await self.fetch_last_measurement()

    async def set_target_temperature(self, temperature):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'max_temp': temperature }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set the target temperature failed with status %i", self._settings_url, resp.status)
                return

            await self.fetch_settings()

    async def set_dsr_enabled(self, enabled):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'dsr_enabled': enabled }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set dsr (grid assistance) enabled failed with status %i", self._settings_url, resp.status)
                return

            await self.fetch_settings()

    async def set_frost_protection_enabled(self, enabled):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'frost_protection_enabled': enabled }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set frost protection enabled failed with status %i", self._settings_url, resp.status)
                return

            await self.fetch_settings()

    async def set_distributed_computing_enabled(self, enabled):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'distributed_computing_enabled': enabled }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set distributed computing (medical research) enabled failed with status %i", self._settings_url, resp.status)
                return

            await self.fetch_settings()

    async def set_cleansing_temperature(self, value):

        # Ensure values are within correct range
        value = min(value, 55)
        value = max(value, 51)

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'cleansing_temperature': value }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set cleansing temperature failed with status %i", self._settings_url, resp.status)
                return

            await self.fetch_settings()

    async def set_divert_exported_enabled(self, enabled):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'divert_exported_enabled': enabled }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set divert export enabled failed with status %i", self._settings_url, resp.status)
                return

            await self.fetch_settings()

    async def set_pv_cut_in_threshold(self, value):

        # Ensure values are within correct range
        value = min(value, 500)
        value = max(value, 0)

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'pv_cut_in_threshold': value }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set PV cut in threshold failed with status %i", self._control_url, resp.status)
                return

            await self.fetch_settings()

    async def set_pv_charge_limit(self, value):

        # Ensure values are within correct range
        value = min(value, 100)
        value = max(value, 0)

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'pv_charge_limit': value }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set PV charge limit failed with status %i", self._control_url, resp.status)
                return

            await self.fetch_settings()

    async def set_pv_target_current(self, value):

        # Ensure values are within correct range
        value = min(value, 0)
        value = max(value, -1)

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'pv_target_current': value }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set PV target current failed with status %i", self._control_url, resp.status)
                return

            await self.fetch_settings()

    async def set_pv_over_temperature(self, value):

        # Ensure values are within correct range
        value = min(value, 60)
        value = max(value, 45)

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._settings_url, headers=headers, json={'pv_over_temperature': value }) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set PV over temperature failed with status %i", self._control_url, resp.status)
                return

            await self.fetch_settings()

    async def authenticate(self):

        if self._token:
            _LOGGER.info("Authentication token is valid")
            return

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        async with session.get(ROOT_ENDPOINT) as resp:

            if resp.status != 200:
                _LOGGER.error("Fetch of root at %s failed with status code %i", ROOT_ENDPOINT, resp.status)
                return False

            root_result = await resp.json()

            self._account_url = root_result["_links"]["account"]["href"]

            _LOGGER.info("Account URL: %s", self._account_url)

            async with session.get(self._account_url) as resp:

                if resp.status != 200:
                    _LOGGER.error("Fetch of account at %s failed with status code %i", self._account_url, resp.status)
                    return False

                account_result = await resp.json()

                self._login_url = account_result["_links"]["login"]["href"]

                _LOGGER.info("Login URL: %s", self._login_url)

        async with session.post(self._login_url, json={'username': self.username, 'password': self.password}) as resp:

            if resp.status != 201:
                _LOGGER.error("Authentication failed with status code %i", resp.status)
                return False

            login_result = await resp.json()
            token = login_result['token']
            self._token = token
            return True

    async def fetch_tank_information(self):

        if self._latest_measurement_url:
            _LOGGER.info("Tank information has already been fetched")
            return

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.get(ROOT_ENDPOINT, headers=headers) as resp:

            if resp.status != 200:
                _LOGGER.error("Fetch of root at %s failed with status code %i", ROOT_ENDPOINT, resp.status)
                return False

            root_result = await resp.json()

            self._tanks_url = root_result["_links"]["tanks"]["href"]

        async with session.get(self._tanks_url, headers=headers) as resp:

            if resp.status != 200:
                _LOGGER.error("Fetch of tanks at %s failed with status code %i", self._tanks_url, resp.status)
                return False

            tank_result = await resp.json()

            tanks = tank_result['_embedded']['tankList']

            _LOGGER.debug(tanks)

            tank = None

            for i, subjobj in enumerate(tanks):
                if self.serial_number == subjobj['serialNumber']:
                    _LOGGER.info("Found a tank with matching serial number %s!", self.serial_number)
                    tank = subjobj
                    break

            if not tank:
                _LOGGER.error("Could not find a tank with the serial number %s", self.serial_number)
                return False

            tank_url = tank["_links"]["self"]["href"]
            self.firmwareVersion = tank["firmwareVersion"]

            async with session.get(tank_url, headers=headers) as resp:

                if resp.status != 200:
                    _LOGGER.error("Fetch of the tanks details at %s failed with status %i", tank_url, resp.status)
                    return False

                tank_url_result = await resp.json()

                _LOGGER.debug(tank_url_result)

                self._latest_measurement_url = tank_url_result["_links"]["latest_measurement"]["href"]
                self._control_url = tank_url_result["_links"]["control"]["href"]
                self._settings_url = tank_url_result["_links"]["settings"]["href"]
                self._schedule_url = tank_url_result["_links"]["schedule"]["href"]

                self.modelCode = tank_url_result["tankModelCode"]

                tank_configuration_json = tank_url_result["configuration"]
                tank_configuration = json.loads(tank_configuration_json)
                
                # Some tanks do not return a mixergyPvType - so force to NO_INVERTER
                tank_configuration_pvtype = tank_configuration.get("mixergyPvType", "NO_INVERTER")
                self._has_pv_diverter = (tank_configuration_pvtype != "NO_INVERTER")

                _LOGGER.debug("Measurement URL is %s", self._latest_measurement_url)
                _LOGGER.debug("Control URL is %s", self._control_url)
                _LOGGER.debug("Settings URL is %s", self._settings_url)
                _LOGGER.debug("Schedule URL is %s", self._schedule_url)

                return True

    async def fetch_last_measurement(self):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.get(self._latest_measurement_url, headers=headers) as resp:

            if resp.status != 200:
                _LOGGER.info("Fetch of the latest measurement at %s failed with status %i", self._latest_measurement_url, resp.status)
                return

            tank_result = await resp.json()
            _LOGGER.debug(tank_result)

            self._hot_water_temperature = tank_result["topTemperature"]
            self._coldest_water_temperature = tank_result["bottomTemperature"]

            if "pvEnergy" in tank_result:
                self._pv_power = tank_result["pvEnergy"] / 60000
            else:
                self._pv_power = 0

            if "clampPower" in tank_result:
                self._clamp_power = tank_result["clampPower"]
            else:
                self._clamp_power = 0

            new_charge = tank_result["charge"]

            _LOGGER.debug("Current: %f", self._charge)
            _LOGGER.debug("New: %f", new_charge)

            if new_charge != self._charge:
                _LOGGER.debug('Sending charge_changed event')

                event_data = {
                    "device_id": self._id,
                    "type": "charge_changed",
                    "charge" : new_charge
                }

                self._hass.bus.async_fire("mixergy_event", event_data)

            self._charge = new_charge

            # Fetch information about the current state of the heating.

            state = json.loads(tank_result["state"])

            current = state["current"]

            new_target_charge = 0

            if "target" in current:
                new_target_charge = current["target"]
            else:
                new_target_charge = 0

            self._target_charge = new_target_charge

            vacation = False

            # Source is only present when vacation is enabled it seems
            if "source" in current:
                source = current["source"]
                vacation = source == "Vacation"

            if vacation:
                self._in_holiday_mode = True

                # Assume it's all off as the tank is in holiday mode
                self._electric_heat_source = False
                self._heatpump_heat_source = False
                self._indirect_heat_source = False

            else:
                self._in_holiday_mode = False

                heat_source = current["heat_source"].lower()
                heat_source_on = current["immersion"].lower() == "on"

                if heat_source == "indirect":
                    self._electric_heat_source = False
                    self._heatpump_heat_source = False
                    self._indirect_heat_source = heat_source_on

                elif heat_source == "electric":
                    self._electric_heat_source = heat_source_on
                    self._indirect_heat_source = False
                    self._heatpump_heat_source = False

                elif heat_source == "heatpump":
                    self._heatpump_heat_source = heat_source_on
                    self._indirect_heat_source = False
                    self._electric_heat_source = False

                else:
                    self._indirect_heat_source = False
                    self._electric_heat_source = False
                    self._heatpump_heat_source = False

    async def fetch_settings(self):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.get(self._settings_url, headers=headers) as resp:

            if resp.status != 200:
                _LOGGER.info("Fetch of the settings %s failed with status %i", self._settings_url, resp.status)
                return

            # The settings API returns text/plain as the content-type, so using the resp.json() fails.
            # Load it as a bit of JSON via the text.
            response_text = await resp.text()
            json_object = json.loads(response_text)
            _LOGGER.debug(json_object)

            self._target_temperature = json_object["max_temp"]
            self._dsr_enabled = json_object["dsr_enabled"]
            self._frost_protection_enabled = json_object["frost_protection_enabled"]
            self._distributed_computing_enabled = json_object["distributed_computing_enabled"]
            self._cleansing_temperature = json_object["cleansing_temperature"]

            try:
                self._divert_exported_enabled = json_object["divert_exported_enabled"]
                self._pv_charge_limit = json_object["pv_charge_limit"]
                self._pv_cut_in_threshold = json_object["pv_cut_in_threshold"]
                self._pv_target_current = json_object["pv_target_current"]
                self._pv_over_temperature = json_object["pv_over_temperature"]
            except KeyError:
                pass

    async def fetch_schedule(self):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.get(self._schedule_url, headers=headers) as resp:

            if resp.status != 200:
                _LOGGER.info("Fetch of the schedule %s failed with status %i", self._schedule_url, resp.status)
                return

            # The schedule API returns text/plain as the content-type, so using the resp.json() fails.
            # Load it as a bit of JSON via the text.
            response_text = await resp.text()
            json_object = json.loads(response_text)
            _LOGGER.debug(json_object)

            self._schedule = json_object

    async def set_schedule(self, value):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self._token}'}

        async with session.put(self._schedule_url, headers=headers, json=value) as resp:

            if resp.status != 200:
                _LOGGER.error("Call to %s to set schedule failed with status %i", self._schedule_url, resp.status)
                return

            await self.fetch_schedule()

    async def set_holiday_dates(self, start_date: datetime, end_date: datetime):

        await self.fetch_schedule()

        schedule = self._schedule

        if schedule == None:
            _LOGGER.error("Tried to set holiday dates but no schedule to set")
            return

        schedule["holiday"] = {
            "departDate": int(start_date.timestamp()) * 1000,
            "returnDate": int(end_date.timestamp()) * 1000
        }

        await self.set_schedule(schedule)

        await self.publish_updates()

    async def clear_holiday_dates(self):

        await self.fetch_schedule()

        schedule = self._schedule

        if schedule == None:
            _LOGGER.error("Tried to clear holiday dates but no schedule to set")
            return

        schedule.pop("holiday", None)

        await self.set_schedule(schedule)

        await self.publish_updates()

    async def fetch_data(self):

        _LOGGER.info('Fetching data....')

        await self.authenticate()

        await self.fetch_tank_information()

        await self.fetch_last_measurement()

        await self.fetch_settings()

        await self.fetch_schedule()

        await self.publish_updates()

    def register_callback(self, callback):
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        self._callbacks.discard(callback)

    async def publish_updates(self):
        for callback in self._callbacks:
            callback()

    @property
    def online(self):
        return True

    @property
    def hot_water_temperature(self):
        return self._hot_water_temperature

    @property
    def coldest_water_temperature(self):
        return self._coldest_water_temperature

    @property
    def charge(self):
        return self._charge

    @property
    def target_charge(self):
        return self._target_charge

    @property
    def indirect_heat_source(self):
        return self._indirect_heat_source

    @property
    def electic_heat_source(self):
        return self._electric_heat_source

    @property
    def in_holiday_mode(self):
        return self._in_holiday_mode

    @property
    def heatpump_heat_source(self):
        return self._heatpump_heat_source

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def dsr_enabled(self):
        return self._dsr_enabled

    @property
    def frost_protection_enabled(self):
        return self._frost_protection_enabled

    @property
    def distributed_computing_enabled(self):
        return self._distributed_computing_enabled

    @property
    def cleansing_temperature(self):
        return self._cleansing_temperature

    @property
    def pv_power(self):
        return self._pv_power

    @property
    def clamp_power(self):
        return self._clamp_power

    @property
    def has_pv_diverter(self):
        return self._has_pv_diverter

    @property
    def divert_exported_enabled(self):
        return self._divert_exported_enabled

    @property
    def pv_cut_in_threshold(self):
        return self._pv_cut_in_threshold

    @property
    def pv_charge_limit(self):
        return self._pv_charge_limit

    @property
    def pv_target_current(self):
        return self._pv_target_current

    @property
    def pv_over_temperature(self):
        return self._pv_over_temperature

    @property
    def holiday_date_start(self) -> Optional[datetime]:
        try:
            return datetime.fromtimestamp(self._schedule["holiday"]["departDate"] / 1000)
        except KeyError:
            return None
        except TypeError:
            return None

    @property
    def holiday_date_end(self) -> Optional[datetime]:
        try:
            return datetime.fromtimestamp(self._schedule["holiday"]["returnDate"] / 1000)
        except KeyError:
            return None
        except TypeError:
            return None