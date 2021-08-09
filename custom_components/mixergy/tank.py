import logging
import asyncio
import random
from homeassistant.helpers import aiohttp_client

_LOGGER = logging.getLogger(__name__)

ROOT_ENDPOINT = "https://www.mixergy.io/api/v2"

class Tank:

    manufacturer = "Mixergy Ltd"

    def __init__(self, hass, username, password, serial_number):
        self._id = serial_number.lower()
        self.username = username
        self.password = password
        self.serial_number = serial_number
        self._hass = hass
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._hot_water_temperature = 0
        self._coldest_water_temperature = 0
        self.model = "Mixergy 123"
        self.firmware_version = "0.0.{}".format(random.randint(1, 9))

    @property
    def tank_id(self):
        return self._id

    def set_token(self, token):
        self.__token = token

    def set_tank_url(self, tank_url):
        self.__tank_url = tank_url

    def set_bottom_temperature(self, bottom_temperature):
        self.__bottom_temperature = bottom_temperature

    def set_top_temperature(self, top_temperature):
        self.__top_temperature = top_temperature

    def set_charge(self, charge):
        self.__charge = charge

    async def test_connection(self):
        return True

    async def fetchUrls(self):
        _LOGGER.info("Fetching the API endpoints...")
        async with session.post("https://www.mixergy.io/api/v2") as resp:
            login_result = await resp.json()
            _LOGGER.info(login_result)
            token = login_result['token']
            self.set_token(token)

    async def authenticate(self):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        async with session.post("https://www.mixergy.io/api/v2/account/login", json={'username':self.username, 'password':self.password}) as resp:
            login_result = await resp.json()
            _LOGGER.info(login_result)
            token = login_result['token']
            self.set_token(token)

    async def fetch_tank_information(self):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self.__token}'}

        _LOGGER.info(headers)

        async with session.get("https://www.mixergy.io/api/v2/tanks", headers=headers) as resp:
            _LOGGER.info(resp.status)
            tank_result = await resp.json()
            _LOGGER.info(tank_result)

            # Grab the first tank for now. We will update this to match by the specified serial number in the future!!
            tanks = tank_result['_embedded']['tankList']
            tank = tanks[0]
            tank_url = tank["_links"]["self"]["href"]
            self.set_tank_url(tank_url)
            self.firmwareVersion = tank["firmwareVersion"]
            self.modelCode = tank["tankModelCode"]

    async def fetch_last_measurement(self):

        session = aiohttp_client.async_get_clientsession(self._hass, verify_ssl=False)

        headers = {'Authorization': f'Bearer {self.__token}'}

        async with session.get(self.__tank_url,headers=headers) as resp:
            _LOGGER.info(resp.status)
            tank_result = await resp.json()
            _LOGGER.info(tank_result)
            last_measurement_url = tank_result["_links"]["latest_measurement"]["href"]

            async with session.get(last_measurement_url,headers=headers) as resp:
                tank_result = await resp.json()
                _LOGGER.info(tank_result)
                self.set_top_temperature(tank_result["topTemperature"])
                self.set_bottom_temperature(tank_result["bottomTemperature"])
                self.set_charge(tank_result["charge"])

    async def fetch_data(self):

        await self.authenticate()

        await self.fetch_tank_information()

        await self.fetch_last_measurement()

        await self.publish_updates()

        return { "hot_water_temperature": 40 }

    def register_callback(self, callback):
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        self._callbacks.discard(callback)

    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self):
        for callback in self._callbacks:
            callback()

    @property
    def online(self):
        return True

    @property
    def hot_water_temperature(self):
        return self.__top_temperature

    @property
    def coldest_water_temperature(self):
        return self.__bottom_temperature

    @property
    def charge(self):
        return self.__charge