import subprocess
import concurrent.futures
import asyncio
import logging
import websockets
import time
import imageio
import cv2
import numpy as np
from nes_py.wrappers import JoypadSpace
from nes_py import NESEnv

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
    global execution_count, last_reset_time
    # Reset the emulator
    state = emulator.reset()

    # Emulation loop and livestreaming
    done = False
    while not done:
        # Process frame
        global current_action
        state, _, done, _ = emulator.step(action=current_action)
        state = state.astype('uint8')

        # Render the emulator state in a window
        emulator.render()

        # Convert state to PNG and send over websocket
        failed_sockets = set()
        for websocket in frame_websockets:
            try:
                png_data = imageio.imwrite(imageio.RETURN_BYTES, state, format='png')
                await websocket.send(png_data)
                #await websocket.send(f"A frame at {str(time.time())}")
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
        await asyncio.sleep(1.0 / 30.0)


# Start the event loop
async def main():
    # Start the WebSocket servers and the emulation concurrently
    await asyncio.gather(start_controller_websocket_server(), start_frame_websocket_server(), start_emulation())

asyncio.run(main())
