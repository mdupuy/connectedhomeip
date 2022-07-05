#!/usr/bin/env python3
import asyncio
import re
from websockets import client as ws
import sys

#import avh_api_async as AvhAPIAsync
from pprint import pprint

url = sys.argv[1]

stage = 1
done = False
async def configureInstance():
  global done
  text = ''

  # Give the VM time to finish booting
  console = await ws.connect(url)

  async def handleText(text):
    global done, stage

    if stage == 1:
      # Log in
      match = re.match(r'(?:(raspberrypi login:)|(Password:)|.*(pi\@raspberrypi:~\$))', text) 
      if (match):
        pprint(match)
        if match[1]:
          await console.send('pi\n')
        elif match[2]:
          await console.send('raspberry\n')
        elif match[3]:
          print('== Logged in ==')
          # Hit enter to let the network code continue
          await console.send('\n')
          stage += 1
        return True
    elif stage == 2:
      # Ensure network is connected, then kick off package installations
      match = re.match(r'(?:.*(pi\@raspberrypi:~\$)|.*default via (\S+) dev eth0)', text)
      if (match):
        if (match[1]):
          await asyncio.sleep(1)
          await console.send('ip route\n')
        elif (match[2]):
          stage += 1
          await console.send((
            'sudo apt-get update && ',
            'sudo apt-get -y install docker.io curl jq && ',
            'echo "PACKAGE INSTALLATION SUCCESS" || echo "PACKAGE INSTALLATION FAILED"\n'))
        return True
    elif stage == 3:
      # Watch for package installation success
      match = re.match(r'(?:.*(?<!echo ")(PACKAGE INSTALLATION SUCCESS)|.*(?<!echo ")(PACKAGE INSTALLATION FAILED))', text)
      if (match):
        if (match[1]):
          stage += 1
        elif (match[2]):
          raise Exception('Package installation failed')
        return True
    elif stage == 4:
      # Install github runner
      match = re.match(r'(?:.*(pi\@raspberrypi:~\$))', text)
      if match:
        await console.send('curl -s https://raw.githubusercontent.com/actions/runner/main/scripts/create-latest-svc.sh | sed -e "s/-x64-/-arm64-/g" | RUNNER_CFG_PAT="%s" bash -s -- -s "%s" -n "avhrunner"\n' % (githubPat, runnerScope))
        stage += 1
    elif stage == 5:
      match = re.match(r'(?:.*error: (Failed to get a token)|.*(Started GitHub Actions Runner))', text)
      if match:
        if match[1]:
          raise Exception('Failed to register github runner with github, invalid github token or scope?')
        elif match[2]:
          # Success
          stage += 1
    else:
      match = re.match(r'(?:.*(pi\@raspberrypi:~\$))', text)
      if (match):
        done = True
    return False
  try:
    async for message in console:

      data = message.decode('UTF-8', errors='ignore')
      text += data

      while '\n' in text:
        offset = text.find('\n')
        line, text = text[:offset], text[offset+1:]
        print('%s' % line)
        await handleText(line)
      
      if await handleText(text):
        # Clear partial lines that were matched
        print('%s' % text, end='')
        text = ''
      
      if done:
        break

  finally:
    console.close_timeout = 1
    await console.close()


# Defining the host is optional and defaults to https://app.avh.arm.com/api
# See configuration.py for a list of all supported configuration parameters.

exitStatus = 0

async def main():
  global exitStatus
  global api_instance

  print('Connecting to VM and configuring packages')
  await configureInstance()
  print('You can now use your runner')

asyncio.run(main())
exit(0)