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

def cpp_frame_to_string(state: np.ndarray, changed_pixels: list) -> str:
    # Get the path of the Python file
    python_file_path = os.path.abspath(__file__)

    # Get the directory of the Python file
    python_file_directory = os.path.dirname(python_file_path)

    # Construct the shared library path
    shared_library_path = os.path.join(python_file_directory, 'neos-nes-cpp-lib.so')

    # Load the shared library
    mylib = ctypes.CDLL(os.path.abspath(shared_library_path), winmode=0)

    frame_to_string = mylib.frame_to_string
    frame_to_string.argtypes = [ctypes.POINTER(Array3D), ctypes.POINTER(BoolArray), ctypes.c_char_p]
    frame_to_string.restype = None

    # Convert the ndarray to a C-compatible structure
    array = Array3D((state.shape[0], state.shape[1], state.shape[2]), state.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)))

    # Create an empty char array for the output - 61440 pixels * (9 characters for length of rule) * (up to 4 bytes per character)
    output = ctypes.create_string_buffer(61440 * 9 * 4)

    # Call the C++ frame_to_string function
    changed_pixels_arr = BoolArray(state.shape[0] * state.shape[1], (ctypes.c_bool * (state.shape[0] * state.shape[1]))(*changed_pixels))
    frame_to_string(ctypes.byref(array), ctypes.byref(changed_pixels_arr), output)

    # Convert the returned value to a Python string
    string_result = output.value.decode()

    return string_result
