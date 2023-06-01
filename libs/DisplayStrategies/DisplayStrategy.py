from abc import ABC, abstractmethod

from libs.Helpers.GeneralHelpers import *

def rgb_to_utf8(r: int, g: int, b: int, offset: int=0) -> str:
    """Takes an RGB tuple and converts it into a single UTF-8 character"""
    r >>= 2
    g >>= 2
    b >>= 2
    rgb_int = b<<10 | g<<5 | r
    rgb_int += offset
    if rgb_int >= 0xD800:
        rgb_int += SURROGATE_RANGE_SIZE
    return chr(rgb_int)

def utf8_to_rgb(utf8_char: str, offset: int=0) -> tuple:
    """Converts a UTF-8 character to an RGB tuple"""
    rgb_int = ord(utf8_char)
    if rgb_int >= 0xD800:
        rgb_int -= SURROGATE_RANGE_SIZE
    rgb_int -= offset
    r = (rgb_int>>10 & 0x3F) << 2
    g = (rgb_int>>5 & 0x3F) << 2
    b = (rgb_int & 0x3F) << 2
    return (r, g, b)

def update_canvas(message: str, canvas: np.ndarray, offset: int):
    i = 0
    while i < len(message):
        row_start_index, row_range_length = get_start_index_and_range_length(char=message[i], offset=offset)

        # if len(message) > 1000:
        #     print(f"row_start_index: {row_start_index} row_range_length: {row_range_length}")

        i += 1
        color = utf8_to_rgb(utf8_char=message[i], offset=offset)  # Convert the UTF-8 character to RGB
        i += 1
        while i < len(message):  # Check for delimiter A (end of color)
            if message[i] == '\x01':
                i += 1
                if message[i] == '\x02':
                    break
                else:
                    # This is a new color for the same row, and we need to handle its ranges.
                    color = utf8_to_rgb(utf8_char=message[i], offset=offset)  # Convert the UTF-8 character to RGB
                    i += 1
            while i + 1 < len(message) and message[i] != '\x01':
                start, range_length = get_start_index_and_range_length(char=message[i], offset=offset)  # Get the start index of the range and range length
                for j in range(start, start + range_length):
                    for r in range(row_start_index, row_start_index + row_range_length):
                        canvas[r][j] = color
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
        self.canvas = np.zeros((self.new_frame_height, self.new_frame_width, 3), dtype=np.uint8)  # Initialize an empty canvas

    @abstractmethod
    def display(self):
        pass

    @abstractmethod
    def update_canvas(self, message: str, canvas=None):
        pass

    def show_frame_for_messageviewer(self, window_name: str):
        cv2.imshow(window_name, self.canvas)
        return cv2.waitKey(1) & 0xFF

    def get_key_input_for_messageviewer(self, window_name:str):
        key_code = self.show_frame_for_messageviewer(window_name)
        if key_code == 27:  # ESC key
            return 'q'
        elif key_code == ord("a"):  # Left arrow key
            return 'KEY_LEFT'
        elif key_code == ord("s"):  # Right arrow key
            return 'KEY_RIGHT'
        else:
            return ''



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