import asyncio
import websockets
import logging

logger = logging.getLogger(__name__)

class ControllerWebsocket:

    BUTTON_MAP = {
        'a': 1,
        'b': 2,
        'select': 4,
        'start': 8,
        'up': 16,
        'down': 32,
        'left': 64,
        'right': 128,
    }

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.current_action = 0

    async def handle_controller_connection(self, websocket, path):
        logger.info("Controller WebSocket connection established")
        async for message in websocket:
            logger.info(f"Received message: {message}")
            if message == "release":
                self.current_action = 0
            else:
                self.current_action = self.BUTTON_MAP.get(message, self.current_action)

    async def start(self):
        server = await websockets.serve(self.handle_controller_connection, self.host, self.port)
        logger.info(f"Controller WebSocket server started at ws://{self.host}:{self.port}")
        await server.wait_closed()
