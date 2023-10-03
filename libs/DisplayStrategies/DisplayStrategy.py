from abc import ABC, abstractmethod
from ..Helpers.GeneralHelpers import *

## Orig
def rgb_to_utf8(r: int, g: int, b: int, offset: int = 0) -> str:
    """Takes an RGB tuple and converts it into two UTF-8 characters"""
    # Combine the R and G values into one six-digit number, and the B value into a three-digit number
    # rg_int = r * 1000 + g + offset
    # b_int = b + offset

    # r and b are intentionally switched so cv displays them correctly.
    # Above is the "proper" implementation for RGB.
    rg_int = b * 1000 + g + offset
    b_int = r + offset

    if rg_int > 0xD800:
        rg_int += SURROGATE_RANGE_SIZE
    if b_int > 0xD800:
        b_int += SURROGATE_RANGE_SIZE

    # Convert these numbers into their corresponding Unicode code points
    rg_char = chr(rg_int)
    b_char = chr(b_int)

    # Return the two UTF-8 characters as a string
    return rg_char + b_char


def utf8_to_rgb(utf8_chars: str, offset: int = 0) -> tuple:
    """Converts two UTF-8 characters to an RGB tuple"""
    # Convert the UTF-8 characters back into their original numbers
    rg_int = ord(utf8_chars[0])

    if rg_int >= 0xD800:
        rg_int -= SURROGATE_RANGE_SIZE
    rg_int -= offset

    b_int = ord(utf8_chars[1])
    if b_int >= 0xD800:
        b_int -= SURROGATE_RANGE_SIZE
    b_int -= offset

    # Extract the R, G, and B values
    r = rg_int // 1000
    g = rg_int % 1000
    b = b_int

    # r and b are intentionally switched so cv displays them correctly.
    # The "proper" RGB implementation is (r, g, b)
    return (b, g, r)


def update_canvas(message: str, canvas: np.ndarray, offset: int, display_canvas_every_update: bool = False):
    i = 0

    # This flag will help us know when to end the outer loop, if we reach the end of the message
    end_of_message = False

    # Iterate over the entire message
    while i < len(message) and not end_of_message:

        # Each message starts with a character encoding the starting row index and the row range length
        row_start_index, row_range_length = get_start_index_and_range_length(char=message[i], offset=offset)
        i += 1

        # The next two characters represent a color. Convert it to RGB.
        color = utf8_to_rgb(utf8_chars=message[i:i + 2], offset=offset)
        i += 2

        end_of_color = False
        while i < len(message) and not end_of_color:
            if message[i] == '\x01':
                i += 1

                if message[i] == '\x02':
                    end_of_color = True
                else:
                    color = utf8_to_rgb(utf8_chars=message[i:i + 2], offset=offset)
                    i += 2
            else:
                # This will control the innermost loop and is reset with every new loop iteration
                another_color_change = False

                while i < len(message) and message[i] != '\x01' and not another_color_change:
                    if i + 1 >= len(message):
                        end_of_message = True  # We are at the end, so stop the outer loop as well
                        another_color_change = True  # To stop the current loop
                    else:
                        start, range_length = get_start_index_and_range_length(char=message[i], offset=offset)

                        for j in range(start, start + range_length):
                            for r in range(row_start_index, row_start_index + row_range_length):
                                canvas[r][j] = color

                            if display_canvas_every_update:
                                cv2.imshow('update_canvas debug', canvas)
                        i += 1

        i += 1

    return


def get_start_index_and_range_length(char: str, offset: int) -> (int, int):
    combined = ord(char) - offset
    if combined >= 0xD800:
        combined -= SURROGATE_RANGE_SIZE
    start = combined // 1000
    range_length = combined % 1000
    return start, range_length

class DisplayStrategy(ABC):
    def __init__(self, host: str, port: int, scale_percentage: int):
        self.host = host
        self.port = port
        self.scale_percentage = scale_percentage
        self.new_frame_width = int(DEFAULT_FRAME_WIDTH * (self.scale_percentage / 100))
        self.new_frame_height = int(DEFAULT_FRAME_HEIGHT * (self.scale_percentage / 100))
        # new_frame_height is the amount of rows to create
        # new_frame_width is the amount of columns to create
        # 3 RGB channels
        self.reinitialize_canvas()

    @abstractmethod
    def display(self):
        pass

    @abstractmethod
    def update_canvas(self, message: str, canvas=None):
        pass

    def reinitialize_canvas(self):
        self.canvas = np.zeros((self.new_frame_height, self.new_frame_width, 3), dtype=np.uint8)

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
        # TODO: delete this, only here for debug! Is a memory leak!
        messages = []
        while True:
            try:
                async with websockets.connect(uri, max_size=1024 * 1024 * 10) as websocket:
                    while True:
                        message = await websocket.recv()
                        messages.append(message)
                        # Encoding as UTF-8, but in Logix we will decode the RGB character as UTF-32.
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