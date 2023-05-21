import asyncio
import websockets
import logging
from Websockets.BaseWebsocket import BaseWebsocket

logger = logging.getLogger(__name__)

class FrameWebsocket(BaseWebsocket):

    def __init__(self, host, port):
        super().__init__(host, port)
        self.frame_websockets = set()

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

    def frame_to_string(self, frame):
        """Takes a frame and converts it into a message of pixel ranges and colors"""

        last_color = None
        same_color_start = 0
        message = ""
        total_pixels = frame.shape[0] * frame.shape[1]

        for i, pixel in enumerate(frame.reshape(-1, 3)):
            color = self.rgb_to_utf32(*pixel)
            if color != last_color:
                if last_color is not None:
                    message += f"{same_color_start}+{i - 1 - same_color_start}_{last_color}"
                same_color_start = i
                last_color = color

            if i == total_pixels - 1:  # the end of the pixels, add the last color
                message += f"{same_color_start}+{i - same_color_start}_{last_color}"

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
