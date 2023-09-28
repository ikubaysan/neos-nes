import numpy as np
import os
import ctypes
import logging

logger = logging.getLogger(__name__)

class Array3D(ctypes.Structure):
    _fields_ = [
        ("shape", ctypes.c_int * 3),
        ("data", ctypes.POINTER(ctypes.c_ubyte)),
    ]


class BoolArray(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int),
        ("data", ctypes.POINTER(ctypes.c_bool)),
    ]


class FrameToString:
    def __init__(self):
        # Get the path of the Python file
        python_file_path = os.path.abspath(__file__)

        # Get the directory of the Python file
        python_file_directory = os.path.dirname(python_file_path)
        os.chdir(python_file_directory)

        # Construct the shared library path
        shared_library_path = os.path.abspath(os.path.join(python_file_directory, 'neos-nes-cpp-lib.so'))

        if os.path.exists(shared_library_path):
            print(f"Found shared library at {shared_library_path}")
        else:
            raise Exception(f"Shared library does not exist at {shared_library_path}")

        print(f"Using shared_library_path {shared_library_path}")

        # Load the shared library
        self.mylib = ctypes.CDLL((shared_library_path), winmode=0)

        self.frame_to_string = self.mylib.frame_to_string
        self.frame_to_string.argtypes = [ctypes.POINTER(Array3D), ctypes.POINTER(Array3D), ctypes.c_char_p]
        self.frame_to_string.restype = None

    def get_string(self, current_state: np.ndarray, last_state: np.ndarray) -> str:
        # Convert the ndarrays to C-compatible structures
        current_array = Array3D((current_state.shape[0], current_state.shape[1], current_state.shape[2]),
                                current_state.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)))

        # Create an empty char array for the output - 61440 pixels * (9 characters for length of rule) * (up to 4 bytes per character)
        output = ctypes.create_string_buffer(61440 * 9 * 4 * 2)

        if last_state is None:
            self.frame_to_string(ctypes.byref(current_array), None, output)
        else:
            last_array = Array3D((last_state.shape[0], last_state.shape[1], last_state.shape[2]),
                                 last_state.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)))
            self.frame_to_string(ctypes.byref(current_array), ctypes.byref(last_array), output)

        # Convert the returned value to a Python string
        string_result = output.value.decode()

        return string_result


# Usage example:
if __name__ == "__main__":
    frame_to_string = FrameToString()

    current_state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)
    last_state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)

    result = frame_to_string.get_string(current_state, last_state)
    print(result)
