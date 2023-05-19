import asyncio
import logging
import websockets
import keyboard
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket server configuration
HOST = 'localhost'
PORT = 9000

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

# The keys we are interested in
KEYS = list(BUTTON_MAP.keys())

# WebSocket connection
websocket = None

# Define a function that sends a message over WebSocket for each key press
def send_key_presses():
    global websocket
    for key in KEYS:
        def send_key(e):
            if websocket is not None:
                message = BUTTON_MAP[e.name]
                asyncio.run(websocket.send(message))
                logger.info(f"Sent {message} for key {e.name}")
        def release_key(e):
            if websocket is not None:
                asyncio.run(websocket.send("release"))
                logger.info("Sent release for all keys")
        keyboard.on_press_key(key, send_key)
        keyboard.on_release_key(key, release_key)

# Start the event loop
async def main():
    global websocket
    async with websockets.connect(f"ws://{HOST}:{PORT}") as ws:
        websocket = ws
        logger.info(f"Connected to WebSocket at ws://{HOST}:{PORT}")
        while True:  # Keep the connection open
            await asyncio.sleep(1)  # Sleep for a bit to reduce CPU usage

# Run the keyboard listener in a separate thread
threading.Thread(target=send_key_presses, daemon=True).start()

# Run the WebSocket client
asyncio.run(main())