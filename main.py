import asyncio
import logging
import websockets
import time
from operator import itemgetter
from nes_py import NESEnv
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a formatter with the desired format and date format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Create a handler and set the formatter
handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Initialize NES emulator and load ROM
emulator = NESEnv(r"C:\Users\Tay\Desktop\Stuff\Games\emulators\fceux\roms\Super Mario Bros.nes")

# Define button map
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

# Create a shared state for the action
current_action = 0

# WebSocket server configuration
#HOST = 'localhost'
HOST = '10.0.0.147'
CONTROLLER_PORT = 9000
FRAME_PORT = 9001

# WebSockets for frame
frame_websockets = set()

execution_count = 0
last_reset_time = time.time()

# Create a shared state for the action...
advanced_display = True
last_frame = None
last_full_frame_time = time.time()

def rgb_to_index(r, g, b):
    """Takes an RGB tuple and converts it into a single integer"""
    r >>= 2
    g >>= 2
    b >>= 2
    return b << 10 | g << 5 | r  # Swap red and blue channels

def index_to_rgb(index):
    """Takes an integer and converts it back into an RGB tuple"""
    r = (index>>10 & 0x3F) << 2
    g = (index>>5 & 0x3F) << 2
    b = (index & 0x3F) << 2
    return (r, g, b)

def frame_to_message(frame):
    """Takes a frame and converts it into a string of UTF-32 characters"""
    color_to_pixels = dict()
    for i, row in enumerate(frame):
        for j, pixel in enumerate(row):
            color_index = rgb_to_index(*pixel)
            if color_index not in color_to_pixels:
                color_to_pixels[color_index] = []
            color_to_pixels[color_index].append((i, j))

    message = ''
    for color_index, pixels in color_to_pixels.items():
        message += chr(color_index)
        for i, j in pixels:
            # 15 bits for i and 15 bits for j
            message += chr((i << 15) | j)
    return message

def message_to_frame(message):
    """Takes a message and converts it back into a frame"""
    frame = np.zeros((240, 256, 3), dtype=np.uint8)  # Initialize an empty frame
    i = 0
    while i < len(message):
        color_index = ord(message[i])
        color = index_to_rgb(color_index)
        i += 1
        while i < len(message) and ord(message[i]) < 0x10000:
            pixel_index = ord(message[i])
            x = pixel_index >> 15
            y = pixel_index & 0x7FFF
            frame[x][y] = color
            i += 1
    return frame


# WebSocket connection handler for controller
async def handle_controller_connection(websocket, path):
    global current_action
    logger.info("Controller WebSocket connection established")
    # Read and process inputs from WebSocket
    async for message in websocket:
        # Map message to action and update current_action
        logger.info(f"Received message: {message}")
        if message == "release":
            current_action = 0
        else:
            current_action = BUTTON_MAP.get(message, current_action)

# WebSocket connection handler for frame
async def handle_frame_connection(websocket, path):
    frame_websockets.add(websocket)
    logger.info("Frame WebSocket connection established")
    try:
        while True:
            # Wait for a message, but do nothing with it.
            # This keeps the connection open
            _ = await websocket.recv()
    except websockets.exceptions.ConnectionClosed:
        logger.info("Frame WebSocket connection closed")
    finally:
        frame_websockets.remove(websocket)

# Start the WebSocket server for controller
async def start_controller_websocket_server():
    server = await websockets.serve(handle_controller_connection, HOST, CONTROLLER_PORT)
    logger.info(f"Controller WebSocket server started at ws://{HOST}:{CONTROLLER_PORT}")
    await server.wait_closed()

# Start the WebSocket server for frame
async def start_frame_websocket_server():
    server = await websockets.serve(handle_frame_connection, HOST, FRAME_PORT)
    logger.info(f"Frame WebSocket server started at ws://{HOST}:{FRAME_PORT}")
    await server.wait_closed()

async def start_emulation():
    global execution_count, last_reset_time, last_frame, last_full_frame_time
    # Reset the emulator
    state = emulator.reset()

    # Emulation loop and livestreaming
    done = False
    while not done:
        # Process frame
        global current_action
        state, _, done, _ = emulator.step(action=current_action)
        state = state.astype('uint8')

        utf32_data = frame_to_message(frame=state)

        # Log the size of the message in bytes
        message_size_bytes = len(utf32_data)
        logger.info(f"Message size: {message_size_bytes} bytes")

        # Render the emulator state in a window
        emulator.render()

        # Convert state to PNG and send over websocket
        failed_sockets = set()

        if message_size_bytes > 0:
            for websocket in list(frame_websockets):
                try:
                    await websocket.send(utf32_data)
                    pass
                except websockets.exceptions.ConnectionClosedOK:
                    logger.info("Client disconnected")
                    failed_sockets.add(websocket)
                except Exception as e:
                    logger.error(f"Error: {e}")
                    failed_sockets.add(websocket)

        # Remove failed sockets from active set
        frame_websockets.difference_update(failed_sockets)
        # Increment execution count
        execution_count += 1

        # If a second has passed since the last reset, log and reset the execution count
        if time.time() - last_reset_time >= 1.0:
            logger.info(f"frames per second: {execution_count}")
            execution_count = 0
            last_reset_time = time.time()

        # Constant delay for each frame
        await asyncio.sleep(1.0 / 120.0)

# Start the event loop
async def main():
    # Start the WebSocket servers and the emulation concurrently
    await asyncio.gather(start_controller_websocket_server(), start_frame_websocket_server(), start_emulation())

asyncio.run(main())