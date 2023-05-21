import asyncio
import websockets
import logging

logger = logging.getLogger(__name__)

class BaseWebsocket:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def start(self):
        server = await websockets.serve(self.handle_connection, self.host, self.port)
        logger.info(f"{self.__class__.__name__} WebSocket server started at ws://{self.host}:{self.port}")
        await server.wait_closed()

    async def handle_connection(self, websocket, path):
        raise NotImplementedError