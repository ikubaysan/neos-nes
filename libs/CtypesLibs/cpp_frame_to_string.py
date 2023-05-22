import numpy as np
import os
import ctypes


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

        # Construct the shared library path
        shared_library_path = os.path.join(python_file_directory, 'neos-nes-cpp-lib.so')

        # Load the shared library
        self.mylib = ctypes.CDLL(os.path.abspath(shared_library_path), winmode=0)

        self.frame_to_string = self.mylib.frame_to_string
        self.frame_to_string.argtypes = [ctypes.POINTER(Array3D), ctypes.POINTER(BoolArray), ctypes.c_char_p]
        self.frame_to_string.restype = None

    def get_string(self, state: np.ndarray, changed_pixels: list) -> str:
        # Convert the ndarray to a C-compatible structure
        array = Array3D((state.shape[0], state.shape[1], state.shape[2]), state.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)))

        # Create an empty char array for the output - 61440 pixels * (9 characters for length of rule) * (up to 4 bytes per character)
        output = ctypes.create_string_buffer(61440 * 9 * 4)

        # Call the C++ frame_to_string function
        changed_pixels_arr = BoolArray(state.shape[0] * state.shape[1], (ctypes.c_bool * (state.shape[0] * state.shape[1]))(*changed_pixels))
        self.frame_to_string(ctypes.byref(array), ctypes.byref(changed_pixels_arr), output)

        # Convert the returned value to a Python string
        string_result = output.value.decode()

        return string_result


# Usage example:
if __name__ == "__main__":
    frame_to_string = FrameToString()
    state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)
    changed_pixels = [True] * (state.shape[0] * state.shape[1])
    output = ctypes.create_string_buffer(61440 * 9 * 4)

    result = frame_to_string.get_string(state, changed_pixels)
    print(result)
