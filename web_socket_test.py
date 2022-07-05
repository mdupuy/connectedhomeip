#!/usr/bin/env python3
import asyncio
#from websockets import client as ws
import sys
import websockets
from pprint import pprint

#print(len(sys.argv))
url = sys.argv[1]
cmd = ""
if len(sys.argv) > 2:
    cmd = sys.argv[2]

# else:
#     cmd = sys.argv[2]

async def main():
    async with websockets.connect(url) as websocket:
        if not cmd:
            await websocket.send("pi\n")
            answer = await websocket.recv()
            await websocket.send("raspberry\n")
            await websocket.recv()
            await websocket.send("\n")
            await websocket.recv()
        else: 
            cmdn=cmd+"\n"
            await websocket.send(cmdn)
            answer = await websocket.recv()
            #print(answer)

        websocket.close_timeout = 1
        await websocket.close()

asyncio.run(main())


exit(0)