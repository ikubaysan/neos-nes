import asyncio
import websockets
import cv2
import numpy as np
import logging
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

def utf32_to_rgb(utf32_str, offset=16):
    """Converts a UTF-32 string to an RGB tuple"""
    rgb_int = ord(utf32_str) - offset
    r = (rgb_int>>10 & 0x3F) << 2
    g = (rgb_int>>5 & 0x3F) << 2
    b = (rgb_int & 0x3F) << 2
    return (r, g, b)

def decode_color_map(message, offset=16):
    color_map = {}
    i = 0
    while i < len(message):
        mesglen = len(message)
        color = utf32_to_rgb(message[i], offset)
        i += 1
        color_map[color] = []
        while (i < len(message) - 1) and (i + 3 < len(message)):
            start = decode_index(message[i], message[i + 1])
            range_length = ord(message[i + 2])
            skip_length = ord(message[i + 3])

            if range_length != 1:
                range_length -= offset
            if skip_length != 1:
                skip_length -= offset

            color_map[color].append((start, range_length, skip_length))
            i += 4

            if ord(message[i]) != 2:
                pass
                break

        i += 1  # skip the delimiter
    return color_map

def decode_index(char1, char2, offset=16):
    part1 = ord(char1) - offset
    ord_char2 = ord(char2)

    if ord_char2 == 1:
        # is actually 0
        part2 = 0
    else:
        part2 = ord_char2 - offset

    return part1 + part2

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
        color_map = decode_color_map(message)
        for color, ranges in color_map.items():
            for start, range_length, _ in ranges:
                for j in range(start, start + range_length + 1):
                    x, y = j // 256, j % 256  # Convert 1D position back to 2D
                    # Correction to prevent out of array bounds error


                    if x == 240:
                        x = 239
                    elif y == 256:
                        y = 255
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
