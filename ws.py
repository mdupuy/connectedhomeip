#!/usr/bin/env python3
import asyncio
#from websockets import client as ws
import sys
import websockets
from pprint import pprint


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
