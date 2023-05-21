import asyncio
import websockets
import cv2
import numpy as np
import logging
import re
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

def utf32_to_rgb(utf32_str):
    """Converts a UTF-32 string to an RGB tuple"""
    rgb_int = ord(utf32_str)
    r = (rgb_int>>10 & 0x3F) << 2
    g = (rgb_int>>5 & 0x3F) << 2
    b = (rgb_int & 0x3F) << 2
    return (r, g, b)

def string_to_frame(data):
    """Converts a string of UTF-32 characters to a frame (2D array of RGB tuples)"""
    pixels = [utf32_to_rgb(ch) for ch in data]
    return np.array(pixels).reshape(240, 256, 3)


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

class AdvancedDisplayStrategy(DisplayStrategy):
    def __init__(self):
        self.canvas = np.zeros((240, 256, 3), dtype=np.uint8)  # Initialize an empty canvas

    def update_canvas(self, message):
        pixel_ranges = re.findall(r'\d+\+\d+_.', message)
        for pixel_range in pixel_ranges:
            range_str = pixel_range[:-2]
            color_str = pixel_range[-1]

            start, range_length = map(int, range_str.split("+"))
            color = utf32_to_rgb(color_str)
            for i in range(start, start + range_length + 1):
                x, y = i // 256, i % 256  # Convert 1D position back to 2D
                self.canvas[x][y] = color

    def display(self, frame):
        self.update_canvas(frame)
        return self.show_frame(self.canvas, 'NES Emulator Frame Viewer (Canvas)')

    async def receive_frames(self):
        uri = f"ws://{HOST}:{PORT}"
        logger.info(f"Using display strategy: {display_strategy.__class__.__name__}")
        while True:
            try:
                async with websockets.connect(uri, max_size=1024 * 1024 * 10) as websocket:
                    while True:
                        message = await websocket.recv()
                        message_bytes = len(message.encode('utf-8'))
                        logger.info(f"Received message with {message_bytes} bytes, {len(message)} chars.")
                        if not display_strategy.display(message):
                            break
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                logger.info("Trying to reconnect in 3 seconds...")
                await asyncio.sleep(3)


if __name__ == "__main__":
    display_strategy = AdvancedDisplayStrategy()
    asyncio.run(display_strategy.receive_frames())
