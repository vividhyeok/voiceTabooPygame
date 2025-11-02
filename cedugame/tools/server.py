import asyncio
import websockets
import json

clients = set()

async def handler(ws):
    clients.add(ws)
    try:
        async for msg in ws:
            data = json.loads(msg)
            for c in list(clients):
                if c != ws:
                    await c.send(json.dumps(data))
    finally:
        clients.remove(ws)

asyncio.run(websockets.serve(handler, "0.0.0.0", 8765))