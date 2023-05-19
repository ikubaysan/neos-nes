import asyncio
import logging
import websockets
import keyboard
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ControllerClient:
    # Define button map
    BUTTON_MAP = {
        'up': 'up',
        'down': 'down',
        'left': 'left',
        'right': 'right',
        'a': 'a',
        'b': 'b',
        'enter': 'start',
        'space': 'select',
    }

    KEYS = list(BUTTON_MAP.keys())

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.websocket = None

    def send_key_presses(self):
        for key in self.KEYS:
            def send_key(e):
                if self.websocket is not None:
                    message = self.BUTTON_MAP[e.name]
                    asyncio.run(self.websocket.send(message))
                    logger.info(f"Sent {message} for key {e.name}")

            def release_key(e):
                if self.websocket is not None:
                    asyncio.run(self.websocket.send("release"))
                    logger.info("Sent release for all keys")

            keyboard.on_press_key(key, send_key)
            keyboard.on_release_key(key, release_key)

    async def main(self):
        while True:
            try:
                async with websockets.connect(f"ws://{self.host}:{self.port}") as ws:
                    self.websocket = ws
                    logger.info(f"Connected to WebSocket at ws://{self.host}:{self.port}")
                    while True:  # Keep the connection open
                        await asyncio.sleep(1)  # Sleep for a bit to reduce CPU usage
            except Exception as e:
                logger.info(f"A critical error occurred. Retrying in 3 seconds...")
                time.sleep(3)

if __name__ == "__main__":
    # Initialize the controller client
    controller_client = ControllerClient('10.0.0.147', 9000)

    # Run the keyboard listener in a separate thread
    threading.Thread(target=controller_client.send_key_presses, daemon=True).start()

    # Run the WebSocket client
    asyncio.run(controller_client.main())
