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

    def _frame_to_string_common(self, frame, changed_pixels=None) -> str:
        last_color = None
        same_color_start = None
        message = ""
        total_pixels = frame.shape[0] * frame.shape[1]

        # Flatten the frame for simpler iteration
        frame_copy = frame.reshape(-1, 3)

        # If changed_pixels is None, consider all pixels as changed
        if changed_pixels is None:
            changed_pixels = [True] * total_pixels
        else:
            changed_pixels = changed_pixels.reshape(-1)

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

    def full_frame_to_string(self, frame):
        return self._frame_to_string_common(frame)

    def frame_to_string(self, frame):
        # Compare frame to the last frame and find changed pixels
        if self.last_frame is not None:
            changed_pixels = np.any(frame != self.last_frame, axis=-1)
        else:
            changed_pixels = np.ones((frame.shape[0], frame.shape[1]), dtype=bool)

        return self._frame_to_string_common(frame, changed_pixels)

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
