#!/usr/bin/env python3
import asyncio
import sys
import websockets
from pprint import pprint

#Example to log into the default account on a raspberry pi:
# ws.py pi n; ws.py raspberry n

url = sys.argv[1]
cmd = sys.argv[2]
newline = ""
if len(sys.argv) > 3:
    newline = sys.argv[3]


async def main():
    async with websockets.connect(url) as websocket:
    #   cmdn=cmd+newline
    #   print(cmdn)
        await websocket.send(cmd)
        if newline:
            await websocket.send("\n")
        answer = await websocket.recv()
        #print(answer)      

        websocket.close_timeout = 1
        await websocket.close()

asyncio.run(main())


exit(0)
