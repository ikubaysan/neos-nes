import subprocess
import concurrent.futures
import asyncio
import logging
import websockets
import time
from nes_py.wrappers import JoypadSpace
from nes_py import NESEnv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize NES emulator and load ROM
#emulator = NESEnv('./roms/flappy.nes')
#emulator = NESEnv(r"C:\Users\Tay\Desktop\Stuff\Games\emulators\fceux\roms\Super Mario Bros.nes")
emulator = NESEnv(r"C:\Users\Tay\Desktop\Stuff\Games\emulators\fceux\roms\FCControllerTest.nes")

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

# Set up command to invoke FFmpeg
command = [
    'ffmpeg',
    '-y',
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo',
    '-s', '256x240',
    '-pix_fmt', 'rgb24',
    '-r', '10',
    '-i', '-',
    '-c:v', 'libx264',
    '-profile:v', 'baseline',
    '-preset', 'ultrafast',
    '-tune', 'fastdecode',
    '-crf', '35',
    '-pix_fmt', 'yuv420p',
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
    logger.info("Controller WebSocket connection established")
    # Read and process inputs from WebSocket
    async for message in websocket:
        # Map message to action and update current_action
        logger.info(f"Received message: {message}")
        if message == "release":
            current_action = 0
        else:
            current_action = BUTTON_MAP.get(message, current_action)


# Start the WebSocket server
async def start_websocket_server():
    server = await websockets.serve(handle_connection, HOST, PORT)
    logger.info(f"Controller WebSocket server started at ws://{HOST}:{PORT}")
    await server.wait_closed()

# Start the emulation
async def start_emulation():
    # Reset the emulator
    state = emulator.reset()

    # Emulation loop and livestreaming
    done = False
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while not done:
            global current_action
            start_time = time.time()
            logger.info(f"Current action: {current_action}")
            state, _, done, _ = emulator.step(action=current_action)
            state = state.astype('uint8')

            # Write frame to FFmpeg's stdin
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(executor, proc.stdin.write, state.tobytes())

            # Calculate the time taken for the current iteration
            elapsed_time = time.time() - start_time

            # Calculate the delay required for 60 FPS (approximately 0.0167 seconds)
            delay = max(0.0, (1/60) - elapsed_time)

            # Delay for the remaining time until the next frame
            await asyncio.sleep(delay)
    proc.stdin.close()

# Start the event loop
async def main():
    # Start the WebSocket server and the emulation concurrently
    await asyncio.gather(start_websocket_server(), start_emulation())

try:
    asyncio.run(main())
finally:
    # Wait for FFmpeg to finish
    proc.communicate()
