from abc import ABC, abstractmethod
from typing import Union
import numpy as np

from Helpers.GeneralHelpers import *

def rgb_to_utf8(r: int, g: int, b: int, offset=0):
    """Takes an RGB tuple and converts it into a single UTF-8 character"""
    r >>= 2
    g >>= 2
    b >>= 2
    rgb_int = r<<10 | g<<5 | b
    # Adjust if in the Unicode surrogate range
    if 0xD800 <= rgb_int <= 0xDFFF:
        logger.info("Avoiding Unicode surrogate range")
        if rgb_int < 0xDC00:
            rgb_int = 0xD7FF  # Maximum value just before the surrogate range
        else:
            rgb_int = 0xE000  # Minimum value just after the surrogate range
    # TODO: having this here might not be right due to above ifs.
    rgb_int += offset
    return chr(rgb_int)

def utf8_to_rgb(utf8_char: str, offset=0):
    """Converts a UTF-8 character to an RGB tuple"""
    rgb_int = ord(utf8_char)
    rgb_int -= offset
    r = (rgb_int>>10 & 0x3F) << 2
    g = (rgb_int>>5 & 0x3F) << 2
    b = (rgb_int & 0x3F) << 2
    return (r, g, b)

def update_canvas(message: str, canvas: np.ndarray, offset: int):
    height = canvas.shape[0]
    width = canvas.shape[1]

    i = 0
    message_len = len(message)
    while i < len(message):
        row = ord(message[i]) - offset  # Get the row index
        canvas_row = canvas[row]
        i += 1
        color = utf8_to_rgb(message[i], offset=offset)  # Convert the UTF-8 character to RGB
        i += 1
        while i < len(message):  # Check for delimiter A (end of color)
            if message[i] == '\x11':
                # If we've reached delimiter A, we're done applying this color to ranges of columns in the current row.
                i += 1
                if message[i] == '\x12':
                    # If we've reached delimiter B, there are no more colors for this row.
                    break
                else:
                    # Otherwise, the next character represents a new color.
                    color = utf8_to_rgb(message[i], offset=offset)  # Convert the UTF-8 character to RGB
                    i += 1

            while i + 1 < len(message) and message[i] != '\x11':  # Check for delimiters A and B
                start = ord(message[i]) - offset  # Get the start index of the range
                i += 1
                range_length = ord(message[i]) - offset  # Get the length of the range
                #for j in range(start, start + range_length):
                for j in range(start, start + range_length):
                    # While the intuitive access might be self.canvas[row][j], we are using self.canvas[j][row] because
                    # in our case, the j refers to the column of the canvas and row refers to the row.
                    #try:
                    #canvas[j][row] = color  # Update the canvas with the color for each index in the range

                    # if row >= len(canvas):
                    #     print(f"Row too big: {row}")
                    #     break
                    # if j >= len(canvas[row]):
                    #     print(f"j too big: {j}")
                    #     break
                    canvas[row][j] = color
                    # except IndexError:
                    #     print(f"IndexError at j={j}, row={row}. Canvas dimensions are {len(self.canvas)} by {len(self.canvas[0])}")
                i += 1
        i += 1
    return

class DisplayStrategy(ABC):
    def __init__(self, host: str, port: int, scale_percentage: int):
        self.host = host
        self.port = port
        self.scale_percentage = scale_percentage
        self.new_frame_width = int(DEFAULT_FRAME_WIDTH * (self.scale_percentage / 100))
        self.new_frame_height = int(DEFAULT_FRAME_HEIGHT * (self.scale_percentage / 100))
        self.canvas = np.zeros((self.new_frame_width, self.new_frame_height, 3), dtype=np.uint8)  # Initialize an empty canvas

    @abstractmethod
    def display(self):
        pass

    @abstractmethod
    def update_canvas(self, message: str, canvas=None):
        pass

    def show_frame(self, window_name: str):
        # Display the image represented by self.canvas in a window with the specified window_name
        cv2.imshow(window_name, self.canvas)

        # Wait for a key press event and check if the pressed key is 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # If 'q' key is pressed, close all OpenCV windows
            cv2.destroyAllWindows()
            return False  # Return False to indicate program should exit

        return True  # Return True to indicate program should continue

    async def receive_frames(self):
        uri = f"ws://{self.host}:{self.port}"
        logger.info(f"Using display strategy: {self.__class__.__name__}")
        while True:
            try:
                async with websockets.connect(uri, max_size=1024 * 1024 * 10) as websocket:
                    while True:
                        message = await websocket.recv()
                        # Encoding as UTF-8, but in Logix we will decode the RGB character as UTF-8.
                        # This still works because the unicode code points are identical for both.
                        #print(message)
                        message_bytes = len(message.encode('utf-8'))
                        logger.info(f"Received message with {message_bytes} bytes, {len(message)} chars.")
                        self.update_canvas(message=message)
                        if not self.display():
                            break
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                logger.info("Trying to reconnect in 3 seconds...")
                await asyncio.sleep(3)