from asyncio import Queue
from nes_py import NESEnv
from libs.Websockets.ControllerWebsocket import ControllerWebsocket
from libs.Websockets.FrameWebsocket import FrameWebsocket
from libs.Helpers.GeneralHelpers import *
import time
import numpy as np
import cv2

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
    # 60.0 with 100 scale runs fine, but is delayed for the viewer when there is substantial movement.
    MAX_RENDER_FRAME_RATE: float = 60.0
    # TODO: For some reason I'm getting 20 FPS if this is 30, and 30 FPS if this is 40.
    MAX_PUBLISH_FRAME_RATE: float = 60.0
    #MAX_PUBLISH_FRAME_RATE: float = 120.0
    SEND_FULL_FRAMES_ONLY: bool = False
    SCALE_PERCENTAGE: int = 100
    SCALE_INTERPOLATION_METHOD = cv2.INTER_LINEAR
    """
    INTER_NEAREST looks ok but flickers
    INTER_LINEAR looks ok
    INTER_AREA looks ok, has some artifacting
    INTER_CUBIC looks bad
    INTER_LANCZOS4 looks bad
    """

    # Reduces amount of changed pixels, so this can improve FPS.
    SCANLINES_ENABLED: bool = False

    def __init__(self, emulator:NESEnv, host, controller_port, frame_port):
        # WebSocket server configuration
        self.host = host
        self.controller_port = controller_port
        self.frame_port = frame_port

        # Create instances of ControllerWebsocket and FrameWebsocket
        self.controller = ControllerWebsocket(self.host, self.controller_port)
        self.frame = FrameWebsocket(self.host, self.frame_port)

        self.emulator = emulator
        self.execution_count_rendered = 0
        self.execution_count_published = 0

        self.previous_fps_check_time = time.time()

        self.last_full_frame_time = time.time()
        self.full_frame_interval = 5.0  # 5 seconds

        self.last_render_time = time.time()
        self.last_frame_publish_time = time.time()
        self.queue = Queue()

        self.new_frame_width = int(DEFAULT_FRAME_WIDTH * (self.SCALE_PERCENTAGE / 100))
        self.new_frame_height = int(DEFAULT_FRAME_HEIGHT * (self.SCALE_PERCENTAGE / 100))

        logger.info(f"Default frame size: {DEFAULT_FRAME_WIDTH}x{DEFAULT_FRAME_HEIGHT}")
        logger.info(f"Scale percentage: {self.SCALE_PERCENTAGE}%")
        logger.info(f"Scaled frame size: {self.new_frame_width}x{self.new_frame_height}")

    async def main(self):
        # Start the WebSocket servers and the frame production and consumption concurrently
        await asyncio.gather(self.controller.start(), self.frame.start(), self.produce_frames(), self.consume_frames())

    async def produce_frames(self):
        # Reset the emulator
        state = self.emulator.reset()

        # Emulation loop
        done = False
        while not done:
            if time.time() - self.last_render_time < 1.0 / self.MAX_RENDER_FRAME_RATE:
                await asyncio.sleep(0)  # Yield control to the event loop
                continue
            self.last_render_time = time.time()

            state, _, done, _ = self.emulator.step(action=self.controller.current_action)
            # ndarray w/ shape (240, 256, 3)
            # This means a width of 256, height of 240, and 3 color channels. So 256x240x3 for widthXheightXchannels.
            # This is the correct, standard NES resolution: 256x240.
            # The ndarray shape can seem confusing, but think of it as 240 rows and 256 columns.

            if self.SCALE_PERCENTAGE < 100:
                state = cv2.resize(state, (self.new_frame_width, self.new_frame_height), interpolation=self.SCALE_INTERPOLATION_METHOD)

            if self.SCANLINES_ENABLED:
                # Set this RGB value for all pixels
                state[::2, :, :] = 40

                brightening_factor = 1.2  # Adjust this value to achieve the desired brightening effect
                state[1::2, :, :] = np.clip(state[1::2, :, :] * brightening_factor, 0, 255).astype(int)

            # Has enough time has elapsed to publish a frame?
            if time.time() - self.last_frame_publish_time >= 1.0 / self.MAX_PUBLISH_FRAME_RATE:

                state = state.astype('uint8')

                if self.SEND_FULL_FRAMES_ONLY or time.time() - self.last_full_frame_time >= self.full_frame_interval:
                    utf8_data = self.frame.full_frame_to_string(state)
                    self.last_full_frame_time = time.time()
                else:
                    utf8_data = self.frame.frame_to_string(state)

                # Put the frame into the queue
                # Theoretically, if framerate is too high (> 60), the queue could fill up
                # and frames could be produced faster than we send them.
                await self.queue.put(utf8_data)
                self.last_frame_publish_time = time.time()
                self.execution_count_published += 1

            self.emulator.render()
            self.execution_count_rendered += 1

            # If a second has passed since the last reset, log and reset the execution count
            if time.time() - self.previous_fps_check_time >= 1.0:
                logger.info(f"Rendered FPS: {self.execution_count_rendered} Published FPS: {self.execution_count_published}")
                self.execution_count_rendered = 0
                self.execution_count_published = 0
                self.previous_fps_check_time = time.time()

    async def consume_frames(self):
        while True:
            utf8_data = await self.queue.get()  # Wait until a frame is available
            await self.frame.broadcast(utf8_data)  # Send the frame over the websocket

if __name__ == "__main__":
    HOST = '10.0.0.147'
    CONTROLLER_PORT = 9000
    FRAME_PORT = 9001

    #emulator = NESEnv(r"./roms/Super Mario Bros.nes")
    emulator = NESEnv(r"./roms/Sky Kid (USA).nes")
    server = NESGameServer(emulator, HOST, CONTROLLER_PORT, FRAME_PORT)
    asyncio.run(server.main())
