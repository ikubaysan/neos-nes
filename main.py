import asyncio
import logging
from nes_py import NESEnv
from libs.Websockets.ControllerWebsocket import ControllerWebsocket
from libs.Websockets.FrameWebsocket import FrameWebsocket
from Helpers.GeneralHelpers import *
import time

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

speed_profiler = SpeedProfiler()
speed_profiler.start()

# Initialize NES emulator and load ROM

class NESGameServer:
    def __init__(self, emulator:NESEnv, host, controller_port, frame_port):
        # WebSocket server configuration
        self.host = host
        self.controller_port = controller_port
        self.frame_port = frame_port

        # Create instances of ControllerWebsocket and FrameWebsocket
        self.controller = ControllerWebsocket(self.host, self.controller_port)
        self.frame = FrameWebsocket(self.host, self.frame_port)

        self.emulator = emulator
        self.execution_count = 0
        self.previous_fps_check_time = time.time()

        self.last_full_frame_time = time.time()
        self.full_frame_interval = 3.0  # 3 seconds

    async def main(self):
        # Start the WebSocket servers and the emulation concurrently
        await asyncio.gather(self.controller.start(), self.frame.start(), self.start_emulation())

    async def start_emulation(self):
        # Reset the emulator
        state = self.emulator.reset()

        # Emulation loop and livestreaming
        done = False
        while not done:
            # Process frame
            state, _, done, _ = emulator.step(action=self.controller.current_action)
            state = state.astype('uint8')

            if time.time() - self.last_full_frame_time >= self.full_frame_interval:
                utf32_data = self.frame.full_frame_to_string(state)
                self.last_full_frame_time = time.time()
            else:
                utf32_data = self.frame.frame_to_string(state)

            # Log the size of the message in bytes
            message_size_bytes = len(utf32_data)
            logger.info(f"Message size: {message_size_bytes} chars")

            # Render the emulator state in a window
            emulator.render()

            await self.frame.broadcast(utf32_data)

            self.execution_count += 1

            # If a second has passed since the last reset, log and reset the execution count
            if time.time() - self.previous_fps_check_time >= 1.0:
                logger.info(f"frames per second: {self.execution_count}")
                self.execution_count = 0
                self.previous_fps_check_time = time.time()
                # speed_profiler.stop()
                # speed_profiler.start()

            # Constant delay for each frame
            await asyncio.sleep(1.0 / 120.0)


if __name__ == "__main__":
    HOST = '10.0.0.147'
    CONTROLLER_PORT = 9000
    FRAME_PORT = 9001

    emulator = NESEnv(r"./roms/Super Mario Bros.nes")
    server = NESGameServer(emulator, HOST, CONTROLLER_PORT, FRAME_PORT)
    asyncio.run(server.main())
