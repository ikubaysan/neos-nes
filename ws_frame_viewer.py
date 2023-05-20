import asyncio
import websockets
import zlib
import cv2
import numpy as np
import imageio
import logging
import abc
from abc import ABC, abstractmethod

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

#HOST = 'localhost'
HOST = '10.0.0.147'
PORT = 9001

class DisplayStrategy(ABC):
    @abstractmethod
    def display(self, frame):
        pass

    def show_frame(self, frame, window_name):
        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            return False
        return True

class SimpleDisplayStrategy(DisplayStrategy):
    def display(self, frame):
        return self.show_frame(frame, 'NES Emulator Frame Viewer (Simple)')

class CanvasDisplayStrategy(DisplayStrategy):
    def __init__(self):
        self.canvas = np.zeros((240, 256, 3), dtype=np.uint8)  # Initialize an empty canvas

    def display(self, frame):
        for x in range(frame.shape[0]):
            for y in range(frame.shape[1]):
                self.canvas[x, y] = frame[x, y]
        return self.show_frame(self.canvas, 'NES Emulator Frame Viewer (Canvas)')

async def receive_frames(display_strategy: DisplayStrategy):
    uri = f"ws://{HOST}:{PORT}"
    logger.info(f"Using display strategy: {display_strategy.__class__.__name__}")
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                while True:
                    png_data = await websocket.recv()
                    try:
                        frame = imageio.imread(png_data)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
                        resolution = f"{frame.shape[1]}x{frame.shape[0]}"
                        logger.info(f"Received frame with resolution: {resolution}")
                    except:
                        logger.error(f"Could not read data as frame: {png_data}")
                        continue
                    if not display_strategy.display(frame):
                        break
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            logger.info("Trying to reconnect in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    #display_strategy = SimpleDisplayStrategy()
    display_strategy = CanvasDisplayStrategy()
    asyncio.run(receive_frames(display_strategy))
