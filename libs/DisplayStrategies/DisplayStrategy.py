from abc import ABC, abstractmethod
from Helpers.GeneralHelpers import *

def rgb_to_utf32(r: int, g: int, b: int):
    """Takes an RGB tuple and converts it into a single UTF-32 character"""
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
    return chr(rgb_int)

def utf32_to_rgb(utf32_char: str, offset=0):
    """Converts a UTF-32 character to an RGB tuple"""
    rgb_int = ord(utf32_char)
    rgb_int -= offset
    r = (rgb_int>>10 & 0x3F) << 2
    g = (rgb_int>>5 & 0x3F) << 2
    b = (rgb_int & 0x3F) << 2
    return (r, g, b)

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
    def update_canvas(self, message: str):
        pass

    def show_frame(self, window_name: str):
        cv2.imshow(window_name, self.canvas)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            return False
        return True

    async def receive_frames(self):
        uri = f"ws://{self.host}:{self.port}"
        logger.info(f"Using display strategy: {self.__class__.__name__}")
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
                        if not self.display(message):
                            break
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                logger.info("Trying to reconnect in 3 seconds...")
                await asyncio.sleep(3)