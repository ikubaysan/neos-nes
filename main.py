import asyncio
from asyncio import Queue
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
    # 60.0 runs fine, but is delayed for the viewer when there is substantial movement.
    # Now I may need to look into reducing ws message sizes.
    MAX_FRAMERATE = 60.0
    #MAX_FRAMERATE = 35.0
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
        self.full_frame_interval = 5.0  # 5 seconds

        self.last_render_time = time.time()
        self.queue = Queue()

    async def main(self):
        # Start the WebSocket servers and the frame production and consumption concurrently
        await asyncio.gather(self.controller.start(), self.frame.start(), self.produce_frames(), self.consume_frames())

    async def produce_frames(self):
        # Reset the emulator
        state = self.emulator.reset()

        # Emulation loop
        done = False
        while not done:
            if time.time() - self.last_render_time < 1.0 / self.MAX_FRAMERATE:
                await asyncio.sleep(0)  # Yield control to the event loop
                continue
            self.last_render_time = time.time()

            state, _, done, _ = self.emulator.step(action=self.controller.current_action)
            state = state.astype('uint8')

            if time.time() - self.last_full_frame_time >= self.full_frame_interval:
                utf32_data = self.frame.full_frame_to_string(state)
                self.last_full_frame_time = time.time()
            else:
                utf32_data = self.frame.frame_to_string(state)

            # Put the frame into the queue
            # Theoretically, if framerate is too high (> 60), the queue could fill up
            # and frames could be produced faster than we send them.
            await self.queue.put(utf32_data)

            self.emulator.render()

            self.execution_count += 1

            # If a second has passed since the last reset, log and reset the execution count
            if time.time() - self.previous_fps_check_time >= 1.0:
                logger.info(f"frames per second: {self.execution_count}")
                self.execution_count = 0
                self.previous_fps_check_time = time.time()

    async def consume_frames(self):
        while True:
            utf32_data = await self.queue.get()  # Wait until a frame is available
            await self.frame.broadcast(utf32_data)  # Send the frame over the websocket

if __name__ == "__main__":
    HOST = '10.0.0.147'
    CONTROLLER_PORT = 9000
    FRAME_PORT = 9001

    emulator = NESEnv(r"./roms/Super Mario Bros.nes")
    server = NESGameServer(emulator, HOST, CONTROLLER_PORT, FRAME_PORT)
    asyncio.run(server.main())
