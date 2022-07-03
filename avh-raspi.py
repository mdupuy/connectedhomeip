import asyncio
import os
import re
from cmath import pi, sin
import math
from websockets import client as ws
import sys

import avh_api_async as AvhAPI
from pprint import pprint

import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

if len(sys.argv) < 3:
  print('Usage: %s <ApiEndpoint> <ApiToken> [vmName]', sys.argv[0])
  exit(-1)

apiEndpoint = os.environment['ENDPOINT'] #sys.argv[1] #"https://app.avh.arm.com/api"     
apiToken = os.environment['API_TOKEN'] #sys.argv[2] #51f6cc92c0c4c08072a0.93da8450ac6e901a6fa2c95b4f044926623bd92eda46c2cdb54caf97f79851c147a3a900e22e7be50363d2c47d857351fd0faec319b58411895a1fe1819392ce
#if len(sys.argv) > 3:
#  vmName = sys.argv[3]
#else:
vmName = os.environment['INSTANCE1']  #chip-tool
vmName2 = os.environment['INSTANCE2'] #light

async def waitForState(instance, state):
  global api_instance

  instanceState = await api_instance.v1_get_instance_state(instance.id)
  while (instanceState != state):
    if (instanceState == 'error'):
      raise Exception('VM entered error state')
    await asyncio.sleep(1)
    instanceState = await api_instance.v1_get_instance_state(instance.id)

ledStates = [ 'off', 'on' ]
async def printLeds(instance):
  state = await api_instance.v1_get_instance_gpios(instance.id)
  ledBank = state['led'].banks[0]
  print('LED6: %s LED7: %s' % (ledStates[ledBank[0]], ledStates[ledBank[1]]) )

async def pressButton(instance):
  await api_instance.v1_set_instance_gpios(instance.id, {
    "button": {
      "bitCount": 1,
      "banks": [
        [1]
      ]
    }
  })
  await api_instance.v1_set_instance_gpios(instance.id, {
    "button": {
      "bitCount": 1,
      "banks": [
        [0]
      ]
    }
  })

async def testBspImage(instance):
  global api_instance
  global ctx
  temp_low = 20
  temp_high = 30
  press_low = 980
  press_high = 1030
  humid_low = 20
  humid_high = 70

  x = 0.0
  for i in range(3):

    print("\nTest run " + str(i) + "...")

    t_cur = ((25 + math.sin(x) * ((temp_high - temp_low) / 2)) * 4) * 0.25
    t_cur = f'{t_cur:.2f}'

    # Set sensor values...
    print("Setting sensor values : [*] T: " + str(t_cur))
    api_response = await api_instance.v1_set_instance_peripherals(instance.id, {"temperature": t_cur})
    pprint(api_response)

    # Get sensor values...
    p = await api_instance.v1_get_instance_peripherals(instance.id)
    print("Got sensor values : [*] T: " + str(p.temperature))

    if str(p.temperature) != str(t_cur):
      print("FAIL T")

    # TODO
    # ADD WEBSCRAPER TO VALIDATE TEMP MADE IT THROUGH THE WEBSERVER

    # Randomization...
    x += math.pi / 20.0

# Defining the host is optional and defaults to https://app.avh.arm.com/api
# See configuration.py for a list of all supported configuration parameters.

exitStatus = 0

async def main():
  global exitStatus
  global api_instance

  configuration = AvhAPI.Configuration(
      host = apiEndpoint
  )
  # Enter a context with an instance of the API client
  async with AvhAPI.ApiClient(configuration=configuration) as api_client:
    # Create an instance of the API class
    api_instance = AvhAPI.ArmApi(api_client)

    # Log In
    token_response = await api_instance.v1_auth_login({
      "apiToken": apiToken,
    })

    print('Logged in')
    configuration.access_token = token_response.token

    print('Finding a project...')
    api_response = await api_instance.v1_get_projects()
    pprint(api_response)
    projectId = api_response[0].id

    print('Getting our model...')
    api_response = await api_instance.v1_get_models()
    chosenModel = None
    for model in api_response:
      if model.flavor.startswith('rpi4b'):
        chosenModel = model
        break

    pprint(chosenModel)

    print('Finding software for our model...')
    api_response = await api_instance.v1_get_model_software(model.model)
    chosenSoftware = None
    for software in api_response:
      #pprint(software)
      if software.filename.startswith('rpi4b-11.2-lite.coreimg-88715747-93d8-4d48-b8af-94507662df9d'):
        # This software package is compatible with our bsp.elf image
        chosenSoftware = software
        break

    print('Creating a chip-test instance 1...')
    api_response = await api_instance.v1_create_instance({
      "name": vmName,
      "project": projectId,
      "flavor": chosenModel.flavor,
      "os": chosenSoftware.version,
      "osbuild": chosenSoftware.buildid
    })
    instance1 = api_response

    print('Creating a instance 2...')
    api_response = await api_instance.v1_create_instance({
      "name": vmName2,
      "project": projectId,
      "flavor": chosenModel.flavor,
      "os": chosenSoftware.version,
      "osbuild": chosenSoftware.buildid
    })
    instance2 = api_response

    print('Getting VPN Config...')
    api_response = await api_instance.v1_projects_vpnconfig({
      "project": projectId,
      "format": ovpn
    })
    #instance2 = api_response

    error = None
    try:
      print('Waiting for VMs to create...')
      await waitForState(instance1, 'on')
      await waitForState(instance2, 'on')

      print('Setting the VM to use the bsp test software')

    #curl -s -X GET "$AVH_URL/projects/$PROJECT/vpnconfig/ovpn" \
    #-H "Accept: application/json" \
    #-H "Authorization: Bearer $BEARER" > $BASEDIR/avh.ovp
      #api_response = await api_instance.v1_create_image('fwbinary', 'plain', 
      #  name="IOT_HTTP_WebServer.elf",
      #  instance=instance.id,
      #  file=os.path.join(sys.path[0], 'avh-api/python/examples/assets/IOT_HTTP_WebServer.elf')
      #)
      #pprint(api_response)

      #print('Resetting VM to use the new software')
      #api_response = await api_instance.v1_reboot_instance(instance.id)
      #print('Waiting for VM to finish resetting...')
      #await waitForState(instance, 'on')
      #print('done')
      #print('Logging GPIO initial state:')
      #gpios = await api_instance.v1_get_instance_gpios(instance.id)
      #pprint(gpios)
      #print('running test')
      #await testBspImage(instance)
      #print('Logging GPIO final state:')
      #gpios = await api_instance.v1_get_instance_gpios(instance.id)
      #pprint(gpios)

    except Exception as e:      
      print('Encountered error; cleaning up...')
      error = e

    print('Deleting instance...')
    api_response = await api_instance.v1_delete_instance(instance.id)
    api_response = await api_instance.v1_delete_instance(instance2.id)

    if error != None:
      raise error

asyncio.run(asyncio.wait_for(main(), 120))
exit(0)