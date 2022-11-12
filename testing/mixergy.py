import sys
import requests
import json

if len(sys.argv) < 3:
    print("Mixergy username and password required")
    exit()

username = sys.argv[1]
password = sys.argv[2]
serial_number = ''

if len(sys.argv) == 4:
    print("Using Serial Number", sys.argv[3])
    serial_number = sys.argv[3]

# Get login URL

result = requests.get("https://www.mixergy.io/api/v2")

root_result = result.json()

account_url = root_result["_links"]["account"]["href"]

result = requests.get(account_url)

account_result = result.json()

login_url = account_result["_links"]["login"]["href"]

result = requests.post(login_url, json = {'username': username, 'password': password})

if result.status_code != 201:
    print("Authentication failure. Check your credentials and try again!")
    exit()

print("Authentication successful!")

login_result = result.json()

login_token = login_result["token"]

headers = {'Authorization': f'Bearer {login_token}'}

result = requests.get("https://www.mixergy.io/api/v2", headers=headers)

root_result = result.json()

tanks_url = root_result["_links"]["tanks"]["href"]

result = requests.get(tanks_url, headers=headers)

tanks_result = result.json()

tanks = tanks_result['_embedded']['tankList']

if serial_number == '':
    for i, subjobj in enumerate(tanks):
        print("** Found a tank with serial number", subjobj['serialNumber'])
    exit()

for i, subjobj in enumerate(tanks):
    if serial_number == subjobj['serialNumber']:
        print("Found tanks serial number", subjobj['serialNumber'])

        tank_url = subjobj["_links"]["self"]["href"]
        firmware_version = subjobj["firmwareVersion"]
        print("Tank Url:", tank_url)
        print("Firmware:",firmware_version)

        print("Fetching details...")

        result = requests.get(tank_url, headers=headers)

        tank_result = result.json()

        latest_measurement_url = tank_result["_links"]["latest_measurement"]["href"]
        control_url = tank_result["_links"]["control"]["href"]
        modelCode = tank_result["tankModelCode"]

        print("Measurement Url:", latest_measurement_url)
        print("Control Url:", control_url)
        print("Model:",modelCode)

        result = requests.get(latest_measurement_url, headers=headers)

        latest_measurement_result = result.json()

        hot_water_temperature = latest_measurement_result["topTemperature"]
        coldest_water_temperature = latest_measurement_result["bottomTemperature"]
        charge = latest_measurement_result["charge"]

        print("Top Temp:", hot_water_temperature)
        print("Bottom Temp:", coldest_water_temperature)
        print("Charge:",charge)

        state = json.loads(latest_measurement_result["state"])

        current = state["current"]

        heat_source = current["heat_source"]
        heat_source_on = current["immersion"] == "On"

        print("Heat Source:", heat_source)
        print("Heat Source On:", heat_source_on)
