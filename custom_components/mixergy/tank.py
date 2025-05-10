import logging
import aiohttp
import asyncio
import json
import stomp
from datetime import datetime
from typing import Optional
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
from .const import ATTR_CHARGE
from stomp.adapter.ws import websocket

_LOGGER = logging.getLogger(__name__)

ROOT_ENDPOINT = "https://www.mixergy.io/api/v2"
REQUEST_TIMEOUT = 60
STOMP_ENDPOINT = "www.mixergy.io"
STOMP_WS_PATH = "/api/v1/stomp"
STOMP_RETRY_TIMER = 15

class TankUrls:
    def __init__(self, account_url):
        self.account_url = account_url

class Tank:

    manufacturer = "Mixergy Ltd"

    def __init__(self, hass, username, password, serial_number):
        self._hass = hass
        self._session = aiohttp_client.async_get_clientsession(hass, verify_ssl=False)

        # Internal data
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._should_connect = False
        self._stomp_conn: stomp.WSConnection | None = None
        self._stomp_conn_task: asyncio.Task | None = None

        # Parameters
        self.username = username
        self.password = password
        self.serial_number = serial_number.upper()

        # URLs
        self._latest_measurement_url = ""
        self._control_url = ""
        self._settings_url = ""
        self._schedule_url = ""

        # Tank informatiom
        self._id = serial_number.lower()
        self._model_code = ""
        self._firmware_version = "0.0.0"
        self._uuid = ""
        self._token = ""

        # Tank settings
        self._hot_water_temperature = -1
        self._coldest_water_temperature = -1
        self._charge = -1
        self._target_charge = 0
        self._indirect_heat_source = False
        self._electric_heat_source = False
        self._heatpump_heat_source = False
        self._target_temperature = -1
        self._target_temperature_control_enabled = False
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

    @property
    def model_code(self):
        return self._model_code

    @property
    def firmware_version(self):
        return self._firmware_version

    async def test_authentication(self):
        return await self._authenticate()

    async def test_connection(self):
        return await self._fetch_tank_information()

    async def _tank_request_put(self, url, json):

        headers = {'Authorization': f'Bearer {self._token}'}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT), self._session.put(url, headers=headers, json=json) as resp:
                if resp.status != 200:
                    _LOGGER.error("Call to %s failed with status %i", url, resp.status)
                    return False

                return True

        except TimeoutError:
            _LOGGER.debug("Timeout calling %s", url)
            return False
    
    async def set_target_charge(self, charge):

        if await self._tank_request_put(self._control_url, {'charge': charge}):
            await self._fetch_last_measurement()

    async def set_target_temperature(self, temperature):

        if await self._tank_request_put(self._settings_url, {'max_temp': temperature}):
            await self._fetch_settings()

    async def set_target_temperature_control_enabled(self, enabled):

        if await self._tank_request_put(self._settings_url, {'target_temperature_control_enabled': enabled}):
            await self._fetch_settings()

    async def set_dsr_enabled(self, enabled):

        if await self._tank_request_put(self._settings_url, {'dsr_enabled': enabled}):
            await self._fetch_settings()

    async def set_frost_protection_enabled(self, enabled):

        if await self._tank_request_put(self._settings_url, {'frost_protection_enabled': enabled}):
            await self._fetch_settings()

    async def set_distributed_computing_enabled(self, enabled):

        if await self._tank_request_put(self._settings_url, {'distributed_computing_enabled': enabled}):
            await self._fetch_settings()

    async def set_cleansing_temperature(self, value):

        # Ensure values are within correct range
        value = min(value, 55)
        value = max(value, 51)

        if await self._tank_request_put(self._settings_url, {'cleansing_temperature': value}):
            await self._fetch_settings()

    async def set_divert_exported_enabled(self, enabled):

        if await self._tank_request_put(self._settings_url, {'divert_exported_enabled': enabled}):
            await self._fetch_settings()

    async def set_pv_cut_in_threshold(self, value):

        # Ensure values are within correct range
        value = min(value, 500)
        value = max(value, 0)

        if await self._tank_request_put(self._settings_url, {'pv_cut_in_threshold': value}):
            await self._fetch_settings()

    async def set_pv_charge_limit(self, value):

        # Ensure values are within correct range
        value = min(value, 100)
        value = max(value, 0)

        if await self._tank_request_put(self._settings_url, {'pv_charge_limit': value}):
            await self._fetch_settings()

    async def set_pv_target_current(self, value):

        # Ensure values are within correct range
        value = min(value, 0)
        value = max(value, -1)

        if await self._tank_request_put(self._settings_url, {'pv_target_current': value}):
            await self._fetch_settings()

    async def set_pv_over_temperature(self, value):

        # Ensure values are within correct range
        value = min(value, 60)
        value = max(value, 45)

        if await self._tank_request_put(self._settings_url, {'pv_over_temperature': value}):
            await self._fetch_settings()

    @callback
    def start(self):

        self._should_connect = True

        self._start_connection()

    @callback
    def _start_connection(self):

        if not self._should_connect:
            _LOGGER.debug("Not starting STOMP connection")
            return

        async def _connection_runner() -> None:
            _LOGGER.debug("STOMP starting connection")

            # Fetch data before connecting so that we have an up-to-date state
            # since the STOMP connection will only give us changes.
            await self.fetch_data()

            host_tuples = [(STOMP_ENDPOINT, 443)]
            _LOGGER.debug("STOMP creating connection")
            stomp_conn = stomp.WSConnection(host_tuples, ws_path=STOMP_WS_PATH)
            _LOGGER.debug("STOMP connection setting SSL")
            stomp_conn.set_ssl(host_tuples)

            class StompListener(stomp.listener.ConnectionListener):
                def __init__(self, tank: Tank):
                    self._tank = tank

                def on_disconnected(self):
                    _LOGGER.debug("STOMP connection: on_disconnected")
                    self._tank._stomp_conn = None
                    self._tank._hass.loop.call_later(STOMP_RETRY_TIMER, self._tank._start_connection)

                def on_message(self, frame):
                    _LOGGER.debug("STOMP connection: on_message")
                    _LOGGER.debug(frame.body)

                    message = json.loads(frame.body)
                    type = message["type"]
                    payload = message["payload"]

                    if type == "Measurement":
                        self._tank._update_from_latest_measurement(payload)

                    elif type == "Event":
                        event = payload["event"]

                        if event == "Settings":
                            additional = json.loads(payload["additional"])
                            self._tank._update_from_new_settings(additional)

                        elif event == "Schedule":
                            additional = json.loads(payload["additional"])
                            self._tank._update_from_new_schedule(additional)

                        elif event == "State":
                            additional = json.loads(payload["additional"])
                            self._tank._update_from_new_state(additional)

                    self._tank._hass.loop.create_task(self._tank._publish_updates())

            listener = StompListener(self)
            _LOGGER.debug("STOMP connection setting listener")
            stomp_conn.set_listener("listener", listener)

            try:
                headers = {'Token': self._token}

                # We do this dance setting the default timeout to 15, then connecting, then setting
                # the timeout on the underlying socket to `None` because there is no other way to
                # ensure that the call to `connect` doesn't block forever if the connection cannot
                # be made. The dance here will ensure that the call to `connect` times-out if it
                # takes longer than 15 seconds, but then the socket is set to never timeout so that
                # it stays connected forever.
                _LOGGER.debug("STOMP connecting socket")
                websocket_default_timeout = websocket.getdefaulttimeout()
                websocket.setdefaulttimeout(15)
                stomp_conn.connect(headers=headers, with_connect_command=True)
                stomp_conn.transport.socket.timeout = None
                websocket.setdefaulttimeout(websocket_default_timeout)

                _LOGGER.debug("STOMP waiting for transport connection")
                stomp_conn.transport.wait_for_connection(timeout=60)
                _LOGGER.debug("STOMP connected")

                topic = f'/topic/tank/{self._uuid}/poll'
                stomp_conn.subscribe(destination=topic, id=self._id, ack="auto")
                _LOGGER.debug(f"STOMP subscribed to {topic}")

            except stomp.exception.ConnectFailedException:
                _LOGGER.error("Failed to connect to Mixergy STOMP server")
                self._hass.loop.call_later(STOMP_RETRY_TIMER, self._start_connection)

            except Exception as e:
                _LOGGER.error(f"Unexpected exception connecting to Mixergy STOMP server:\n{e}")
                self._hass.loop.call_later(STOMP_RETRY_TIMER, self._start_connection)

            self._stomp_conn = stomp_conn

        self._stomp_conn_task = self._hass.loop.create_task(_connection_runner())

    @callback
    def stop(self):

        _LOGGER.debug("STOMP stopping connection")

        self._should_connect = False

        if self._stomp_conn_task is not None:
            self._stomp_conn_task.cancel()

        if self._stomp_conn is not None:
            self._stomp_conn.disconnect()

    async def _authenticate(self):

        if self._token:
            _LOGGER.info("Authentication token is valid")
            return True

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):

                async with self._session.get(ROOT_ENDPOINT) as resp:

                    if resp.status != 200:
                        _LOGGER.error("Fetch of root at %s failed with status code %i", ROOT_ENDPOINT, resp.status)
                        return False

                    root_result = await resp.json()

                    self._account_url = root_result["_links"]["account"]["href"]

                    _LOGGER.info("Account URL: %s", self._account_url)

                    async with self._session.get(self._account_url) as resp:

                        if resp.status != 200:
                            _LOGGER.error("Fetch of account at %s failed with status code %i", self._account_url, resp.status)
                            return False

                        account_result = await resp.json()

                        self._login_url = account_result["_links"]["login"]["href"]

                        _LOGGER.info("Login URL: %s", self._login_url)

                async with self._session.post(self._login_url, json={'username': self.username, 'password': self.password}) as resp:

                    if resp.status != 201:
                        _LOGGER.error("Authentication failed with status code %i", resp.status)
                        return False

                    login_result = await resp.json()
                    token = login_result['token']
                    self._token = token

                    return True

        except TimeoutError:
            _LOGGER.debug("Timeout while authenticating")

    async def _fetch_tank_information(self):

        _LOGGER.debug("Fetching tank information")

        if self._latest_measurement_url:
            _LOGGER.info("Tank information has already been fetched")
            return

        headers = {'Authorization': f'Bearer {self._token}'}

        async with asyncio.timeout(REQUEST_TIMEOUT), self._session.get(ROOT_ENDPOINT, headers=headers) as resp:

            if resp.status != 200:
                _LOGGER.error("Fetch of root at %s failed with status code %i", ROOT_ENDPOINT, resp.status)
                return False

            root_result = await resp.json()

            self._tanks_url = root_result["_links"]["tanks"]["href"]

        async with asyncio.timeout(REQUEST_TIMEOUT), self._session.get(self._tanks_url, headers=headers) as resp:

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

            async with self._session.get(tank_url, headers=headers) as resp:

                if resp.status != 200:
                    _LOGGER.error("Fetch of the tanks details at %s failed with status %i", tank_url, resp.status)
                    return False

                tank_url_result = await resp.json()

                _LOGGER.debug(tank_url_result)

                self._latest_measurement_url = tank_url_result["_links"]["latest_measurement"]["href"]
                self._control_url = tank_url_result["_links"]["control"]["href"]
                self._settings_url = tank_url_result["_links"]["settings"]["href"]
                self._schedule_url = tank_url_result["_links"]["schedule"]["href"]

                self._uuid = tank_url_result["id"]
                self._model_code = tank_url_result["tankModelCode"]
                self._firmware_version = tank_url_result["firmwareVersion"]

                tank_configuration_json = tank_url_result["configuration"]
                tank_configuration = json.loads(tank_configuration_json)
                self._has_pv_diverter = (tank_configuration["mixergyPvType"] != "NO_INVERTER")

                _LOGGER.debug("Measurement URL is %s", self._latest_measurement_url)
                _LOGGER.debug("Control URL is %s", self._control_url)
                _LOGGER.debug("Settings URL is %s", self._settings_url)
                _LOGGER.debug("Schedule URL is %s", self._schedule_url)

                return True

    async def _fetch_last_measurement(self, publish = False):

        _LOGGER.debug("Fetching last measurement")

        headers = {'Authorization': f'Bearer {self._token}'}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT), self._session.get(self._latest_measurement_url, headers=headers, timeout=REQUEST_TIMEOUT) as resp:

                if resp.status != 200:
                    _LOGGER.info("Fetch of the latest measurement at %s failed with status %i", self._latest_measurement_url, resp.status)
                    return

                _LOGGER.debug(f"Fetching last measurement response:\n{resp.status}\n{resp}")

                tank_result = await resp.json()
                self._update_from_latest_measurement(tank_result)

                if publish:
                    await self._publish_updates()

        except TimeoutError:
            _LOGGER.debug("Timeout fetching last measurement")
        
        except Exception as e:
            _LOGGER.debug(f"Unhandled exception:\n{e}\n{e.with_traceback()}")

    def _update_from_latest_measurement(self, tank_result):

        _LOGGER.debug("Updating with latest measurement data:")
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
        self._update_from_new_state(state)

    def _update_from_new_state(self, state):

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

    async def _fetch_settings(self, publish = False):

        _LOGGER.debug("Fetching settings")

        headers = {'Authorization': f'Bearer {self._token}'}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT), self._session.get(self._settings_url, headers=headers) as resp:

                if resp.status != 200:
                    _LOGGER.info("Fetch of the settings %s failed with status %i", self._settings_url, resp.status)
                    return

                # The settings API returns text/plain as the content-type, so using the resp.json() fails.
                # Load it as a bit of JSON via the text.
                response_text = await resp.text()
                json_object = json.loads(response_text)
                self._update_from_new_settings(json_object)

                if publish:
                    await self._publish_updates()

        except TimeoutError:
            _LOGGER.debug("Timeout fetching settings")

    def _update_from_new_settings(self, json_object):

        _LOGGER.debug("Updating with new settings:")
        _LOGGER.debug(json_object)

        self._target_temperature = json_object["max_temp"]
        self._target_temperature_control_enabled = json_object["target_temperature_control_enabled"]
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

    async def _fetch_schedule(self, publish = False):

        _LOGGER.debug("Fetching schedule")

        headers = {'Authorization': f'Bearer {self._token}'}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT), self._session.get(self._schedule_url, headers=headers) as resp:

                if resp.status != 200:
                    _LOGGER.info("Fetch of the schedule %s failed with status %i", self._schedule_url, resp.status)
                    return

                # The schedule API returns text/plain as the content-type, so using the resp.json() fails.
                # Load it as a bit of JSON via the text.
                response_text = await resp.text()
                json_object = json.loads(response_text)
                self._update_from_new_schedule(json_object)

                if publish:
                    await self._publish_updates()

        except TimeoutError:
            _LOGGER.debug("Timeout fetching schedule")

    def _update_from_new_schedule(self, json_object):

            _LOGGER.debug("Updating with new schedule:")
            _LOGGER.debug(json_object)

            self._schedule = json_object

    async def set_schedule(self, value):

        if await self._tank_request_put(self._schedule_url, value):
            await self._fetch_schedule()

    async def set_holiday_dates(self, start_date: datetime, end_date: datetime):

        await self._fetch_schedule()

        schedule = self._schedule

        if schedule == None:
            _LOGGER.error("Tried to set holiday dates but no schedule to set")
            return

        schedule["holiday"] = {
            "departDate": int(start_date.timestamp()) * 1000,
            "returnDate": int(end_date.timestamp()) * 1000
        }

        await self.set_schedule(schedule)

        await self._publish_updates()

    async def clear_holiday_dates(self):

        await self._fetch_schedule()

        schedule = self._schedule

        if schedule == None:
            _LOGGER.error("Tried to clear holiday dates but no schedule to set")
            return

        schedule.pop("holiday", None)

        await self.set_schedule(schedule)

        await self._publish_updates()

    async def fetch_data(self):

        _LOGGER.info('Fetching data....')

        await self._authenticate()

        await self._fetch_tank_information()

        await self._fetch_last_measurement()

        await self._fetch_settings()

        await self._fetch_schedule()

        await self._publish_updates()

    def register_callback(self, callback):
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        self._callbacks.discard(callback)

    async def _publish_updates(self):
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
    def target_temperature_control_enabled(self):
        return self._target_temperature_control_enabled

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