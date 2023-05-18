import subprocess
import asyncio
import logging
import websockets
from nes_py.wrappers import JoypadSpace
from nes_py import NESEnv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize NES emulator and load ROM
emulator = NESEnv('./roms/flappy.nes')

# Define button map
BUTTON_MAP = {
    'up': 4,
    'down': 5,
    'left': 6,
    'right': 7,
    'a': 0,
    'b': 1,
    'start': 3,
    'select': 2,
}

# Create a shared state for the action
current_action = 0

# Set up command to invoke FFmpeg
command = [
    'ffmpeg',
    '-y',
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo',
    '-s', '256x240',
    '-pix_fmt', 'rgb24',
    '-r', '30',
    '-i', '-',
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-preset', 'ultrafast',
    '-f', 'flv',
    'rtmp://localhost/live/nes_stream',
]

# Create subprocess for FFmpeg
proc = subprocess.Popen(command, stdin=subprocess.PIPE)

# WebSocket server configuration
HOST = 'localhost'
PORT = 9000

# WebSocket connection handler
async def handle_connection(websocket, path):
    global current_action
    logger.info("New WebSocket connection established")
    # Read and process inputs from WebSocket
    async for message in websocket:
        # Map message to action and update current_action
        current_action = BUTTON_MAP.get(message, current_action)

# Start the WebSocket server
async def start_websocket_server():
    async with websockets.serve(handle_connection, HOST, PORT):
        logger.info(f"WebSocket server started at ws://{HOST}:{PORT}")
        await asyncio.Future()

# Start the event loop
async def main():
    # Start the WebSocket server
    server_task = asyncio.create_task(start_websocket_server())
    logger.info("Started websocket.")

    # Reset the emulator
    state = emulator.reset()

    # Emulation loop and livestreaming
    done = False
    while not done:
        global current_action
        # Emulate frame and get RGB data
        state, _, done, _ = emulator.step(current_action)
        state = state.astype('uint8')

        # Write frame to FFmpeg's stdin
        proc.stdin.write(state.tobytes())
        #logger.info("Wrote frame.")

        # Break the loop if needed
        if done:
            state = emulator.reset()
            done = False

    proc.stdin.close()
    # Cancel the WebSocket server task
    server_task.cancel()

try:
    asyncio.run(main())
finally:
    # Wait for FFmpeg to finish
    proc.communicate()
