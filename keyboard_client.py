import asyncio
import logging
import websockets
import keyboard

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

# Define an async function that sends a message over WebSocket for each key press
async def send_key_presses(uri):
    async with websockets.connect(uri) as websocket:
        logger.info(f"Connected to WebSocket at {uri}")
        for key in KEYS:
            async def send_key():
                await websocket.send(BUTTON_MAP[key])
                logger.info(f"Sent {BUTTON_MAP[key]}")
            keyboard.on_press_key(key, lambda _: asyncio.run(send_key()))

# Start the event loop
async def main():
    await send_key_presses(f"ws://{HOST}:{PORT}")

# Run the program
asyncio.run(main())
