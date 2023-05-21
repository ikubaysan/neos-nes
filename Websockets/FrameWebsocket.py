from Websockets.BaseWebsocket import *

logger = logging.getLogger(__name__)

class FrameWebsocket(BaseWebsocket):

    def __init__(self, host, port):
        super().__init__(host, port)
        self.frame_websockets = set()
        self.last_frame = None

    @staticmethod
    def rgb_to_utf32(r, g, b):
        """Takes an RGB tuple and converts it into a single UTF-32 character"""
        r >>= 2
        g >>= 2
        b >>= 2

        rgb_int = b << 10 | g << 5 | r  # Swap red and blue channels

        # Adjust if in the Unicode surrogate range
        if 0xD800 <= rgb_int <= 0xDFFF:
            logger.info("Avoiding Unicode surrogate range")
            if rgb_int < 0xDC00:
                rgb_int = 0xD7FF  # Maximum value just before the surrogate range
            else:
                rgb_int = 0xE000  # Minimum value just after the surrogate range

        return chr(rgb_int)

    def full_frame_to_string(self, frame):
        """Takes a frame and converts it into a message of pixel ranges and colors"""

        # Make a copy of frame to ensure it's not modified elsewhere
        frame_copy = frame.copy()

        last_color = None
        same_color_start = 0
        message = ""
        total_pixels = frame.shape[0] * frame.shape[1]

        # Flatten the frame for simpler iteration
        frame_copy = frame_copy.reshape(-1, 3)

        # Iterate over all pixels
        for i, pixel in enumerate(frame_copy):
            color = self.rgb_to_utf32(*pixel)
            if color != last_color:
                if last_color is not None:
                    message += f"{same_color_start}+{i - 1 - same_color_start}_{last_color}"
                same_color_start = i
                last_color = color

            if i == total_pixels - 1:  # the end of the pixels, add the last color
                message += f"{same_color_start}+{i - same_color_start}_{last_color}"

        # Update the last frame
        self.last_frame = frame.copy()

        return message

    def frame_to_string(self, frame):
        # Make a copy of frame to ensure it's not modified elsewhere
        frame_copy = frame.copy()

        last_color = None
        same_color_start = None
        message = ""
        total_pixels = frame.shape[0] * frame.shape[1]

        # Compare frame to the last frame and find changed pixels
        if self.last_frame is not None:
            changed_pixels = np.any(frame_copy != self.last_frame, axis=-1)
        else:
            changed_pixels = np.ones((frame.shape[0], frame.shape[1]), dtype=bool)

        # Flatten the changed pixels and the frame for simpler iteration
        changed_pixels = changed_pixels.reshape(-1)
        frame_copy = frame_copy.reshape(-1, 3)

        # Iterate over pixels that changed
        for i, (pixel, changed) in enumerate(zip(frame_copy, changed_pixels)):
            color = self.rgb_to_utf32(*pixel)

            if changed and color != last_color:
                if last_color is not None and same_color_start is not None:
                    message += f"{same_color_start}+{i - 1 - same_color_start}_{last_color}"
                same_color_start = i
                last_color = color
            elif not changed and same_color_start is not None:
                message += f"{same_color_start}+{i - 1 - same_color_start}_{last_color}"
                same_color_start = None
                last_color = None

            if i == total_pixels - 1 and same_color_start is not None:  # the end of the pixels, add the last color
                message += f"{same_color_start}+{i - same_color_start}_{last_color}"

        # Update the last frame
        self.last_frame = frame.copy()

        return message

    async def broadcast(self, message):
        message_size_bytes = len(message)
        logger.info(f"Message size: {message_size_bytes} chars")

        if message_size_bytes == 0:
            return

        failed_sockets = set()

        for websocket in list(self.frame_websockets):
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosedOK:
                logger.info("Client disconnected")
                failed_sockets.add(websocket)
            except Exception as e:
                logger.error(f"Error: {e}")
                failed_sockets.add(websocket)

        # Remove failed sockets from active set
        self.frame_websockets.difference_update(failed_sockets)

    async def handle_connection(self, websocket, path):
        self.frame_websockets.add(websocket)
        logger.info("Frame WebSocket connection established")
        try:
            while True:
                _ = await websocket.recv()
        except websockets.exceptions.ConnectionClosed:
            logger.info("Frame WebSocket connection closed")
        finally:
            self.frame_websockets.remove(websocket)
