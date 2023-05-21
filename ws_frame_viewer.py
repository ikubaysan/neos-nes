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

COLOR_MAP = [chr(i) for i in range(0x10000, 0x10000 + 64)]

def utf32_to_rgb(utf32_str):
    """Converts a UTF-32 string to an RGB tuple"""
    color_index = COLOR_MAP.index(utf32_str)
    r = (color_index >> 4) << 2
    g = ((color_index >> 2) & 0x3) << 2
    b = (color_index & 0x3) << 2
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

    def update_canvas(self, changes):
        for (x, y_range), color in changes.items():
            for y in range(y_range[0], y_range[1] + 1):
                self.canvas[x][y] = color

    def display(self, frame):
        changed_pixels = 0
        for x in range(len(frame)):
            for y in range(len(frame[x])):
                pixel_changed = False
                for i in range(len(frame[x][y])):
                    # compare the color channels for this pixel
                    #pixel = frame[x][y]
                    if frame[x][y][i] != self.canvas[x][y][i]:
                        pixel_changed = True
                        break
                if pixel_changed:
                    self.canvas[x][y] = frame[x][y]
                    changed_pixels += 1
        #logger.info(f"Updated {changed_pixels} pixels")
        return self.show_frame(self.canvas, 'NES Emulator Frame Viewer (Canvas)')

    async def receive_frames(self):
        uri = f"ws://{HOST}:{PORT}"
        logger.info(f"Using display strategy: {display_strategy.__class__.__name__}")
        while True:
            try:
                async with websockets.connect(uri, max_size=1024*1024*10) as websocket:
                    while True:
                        message = await websocket.recv()
                        message_bytes = len(message.encode('utf-8'))
                        logger.info(f"Received message with {message_bytes} bytes.")
                        try:
                            frame = string_to_frame(message)
                        except:
                            logger.error(f"Could not read data as change: {message}", exc_info=True)
                            continue
                        if not display_strategy.display(frame):
                            break
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                logger.info("Trying to reconnect in 3 seconds...")
                await asyncio.sleep(3)

if __name__ == "__main__":
    display_strategy = AdvancedDisplayStrategy()
    asyncio.run(display_strategy.receive_frames())
