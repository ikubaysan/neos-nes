import asyncio
import websockets
import cv2
import numpy as np
import logging
from abc import ABC, abstractmethod
from Helpers.GeneralHelpers import *

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

def decode_index(char1, char2):
    return ord(char1) + ord(char2)

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
    SCALE_PERCENTAGE = 100
    def __init__(self):
        self.new_frame_width = int(DEFAULT_FRAME_WIDTH * (self.SCALE_PERCENTAGE / 100))
        self.new_frame_height = int(DEFAULT_FRAME_HEIGHT * (self.SCALE_PERCENTAGE / 100))
        self.canvas = np.zeros((self.new_frame_width, self.new_frame_height, 3), dtype=np.uint8)  # Initialize an empty canvas

    def update_canvas(self, message):
        i = 0
        while i < len(message):
            row = ord(message[i])
            i += 1
            while i < len(message) and message[i] != '\x01':  # check for delimiter A (end of color)
                color = utf32_to_rgb(message[i])
                i += 1
                while i + 1 < len(message) and message[i] not in ('\x01', '\x02'):  # check for delimiters A and B
                    start = ord(message[i])
                    i += 1
                    range_length = ord(message[i])
                    i += 1
                    for j in range(start, start + range_length + 1):
                        self.canvas[row][j] = color
                if i < len(message) and message[i] == '\x02':  # check for delimiter B (end of row)
                    break
                i += 1
            i += 1
        return

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
                        # Encoding as UTF-8, but in Logix we will decode the RGB character as UTF-32.
                        # This still works because the unicode code points are identical for both.
                        print(message)
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
