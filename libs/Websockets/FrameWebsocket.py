import numpy as np

from libs.Websockets.BaseWebsocket import *
from libs.CtypesLibs.CPPFrameToString import FrameToString

logger = logging.getLogger(__name__)

class FrameWebsocket(BaseWebsocket):

    def __init__(self, host, port):
        super().__init__(host, port)
        self.frame_websockets = set()
        self.previous_frame = None
        self.cpp_frame_to_string = FrameToString()

    def _frame_to_string_common(self, current_frame, previous_frame) -> str:
        message = self.cpp_frame_to_string.get_string(current_frame, previous_frame)
        self.previous_frame = current_frame
        return message

    def full_frame_to_string(self, current_frame):
        full_frame_string = self._frame_to_string_common(current_frame, previous_frame=None)
        return full_frame_string

    def frame_to_string(self, current_frame):
        message = self._frame_to_string_common(current_frame, previous_frame=self.previous_frame)
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
