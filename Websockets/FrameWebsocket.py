from Websockets.BaseWebsocket import *
import ctypes
import numpy as np
import os
from numpy.ctypeslib import ndpointer

os.add_dll_directory(r"C:/Users/Tay/Desktop/Stuff/Coding/Repos/my_bitbucket/neos-nes/Websockets/")

logger = logging.getLogger(__name__)

#lib = ctypes.CDLL('frame_to_string_common.so')
#lib = ctypes.cdll.LoadLibrary(r"C:/Users/Tay/Desktop/Stuff/Coding/Repos/my_bitbucket/neos-nes/Websockets/frame_to_string_common.so")


#lib = ctypes.CDLL("frame_to_string_common.so", winmode=0)
lib = ctypes.CDLL("C:/Users/Tay/Desktop/Stuff/Coding/Repos/my_bitbucket/neos-nes/Websockets/frame_to_string_common.so", winmode=1)

# Define the data types of the function's arguments
lib.frame_to_string_common.argtypes = [ndpointer(ctypes.c_uint8, flags="C_CONTIGUOUS"),
                                       ctypes.c_int,
                                       ndpointer(ctypes.c_bool, flags="C_CONTIGUOUS"),
                                       ctypes.c_int]

# Define the return type of the function
lib.frame_to_string_common.restype = ctypes.c_char_p

def frame_to_string_common(frame, changed_pixels):
    # Ensure numpy arrays are C-contiguous
    frame = np.ascontiguousarray(frame, dtype=np.uint8)
    changed_pixels = np.ascontiguousarray(changed_pixels, dtype=np.bool)

    # Convert frame and changed_pixels to 1D arrays before passing to C function
    frame = frame.reshape(-1, 3)
    changed_pixels = changed_pixels.reshape(-1)

    # Call the C++ function and decode the result
    result = lib.frame_to_string_common(frame, len(frame), changed_pixels, len(changed_pixels))
    return result.decode()


class FrameWebsocket(BaseWebsocket):

    def __init__(self, host, port):
        super().__init__(host, port)
        self.frame_websockets = set()
        self.last_frame = None

    def full_frame_to_string(self, frame):
        return frame_to_string_common(frame, changed_pixels=None)

    def frame_to_string(self, frame):
        # Compare frame to the last frame and find changed pixels
        if self.last_frame is not None:
            changed_pixels = np.any(frame != self.last_frame, axis=-1)
        else:
            changed_pixels = np.ones((frame.shape[0], frame.shape[1]), dtype=bool)

        message = frame_to_string_common(frame, changed_pixels)
        self.last_frame = frame
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
