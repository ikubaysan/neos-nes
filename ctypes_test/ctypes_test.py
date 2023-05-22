import numpy as np
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


def create_and_process_array():
    # Load the shared library
    mylib = ctypes.CDLL('./mylib.so', winmode=0)

    # Define the function prototype
    process_array = mylib.process_array
    process_array.argtypes = [ctypes.POINTER(Array3D)]
    process_array.restype = ctypes.c_char_p

    frame_to_string = mylib.frame_to_string
    frame_to_string.argtypes = [ctypes.POINTER(Array3D), ctypes.POINTER(BoolArray)]
    frame_to_string.restype = ctypes.c_char_p

    # Create a 3D ndarray
    state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)

    # Make all values multiples of 4
    state = np.floor_divide(state, 4) * 4

    # Convert the ndarray to a C-compatible structure
    array = Array3D((state.shape[0], state.shape[1], state.shape[2]), state.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)))

    # Call the C++ function
    result = process_array(ctypes.byref(array))

    # Convert the returned value to a Python string
    string_result = result.decode()

    # Print the string
    print(string_result)

    # Call the C++ frame_to_string function
    changed_pixels = BoolArray(state.shape[0] * state.shape[1], (ctypes.c_bool * (state.shape[0] * state.shape[1]))(*[True]*state.shape[0]*state.shape[1]))
    result = frame_to_string(ctypes.byref(array), ctypes.byref(changed_pixels))

    # Convert the returned value to a Python string
    string_result = result.decode()

    # Print the string
    print(string_result)


if __name__ == "__main__":
    create_and_process_array()
