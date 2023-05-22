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

    frame_to_string = mylib.frame_to_string
    frame_to_string.argtypes = [ctypes.POINTER(Array3D), ctypes.POINTER(BoolArray), ctypes.c_char_p]
    frame_to_string.restype = None

    # Create a 3D ndarray
    state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)

    # Make all values multiples of 4
    state = np.floor_divide(state, 4) * 4

    # Convert the ndarray to a C-compatible structure
    array = Array3D((state.shape[0], state.shape[1], state.shape[2]), state.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)))

    # Create an empty char array for the output - 61440 pixels * (9 characters for length of rule) * (up to 4 bytes per character)
    output = ctypes.create_string_buffer(61440 * 9 * 4)

    # Call the C++ frame_to_string function
    changed_pixels = BoolArray(state.shape[0] * state.shape[1], (ctypes.c_bool * (state.shape[0] * state.shape[1]))(*[True]*state.shape[0]*state.shape[1]))
    frame_to_string(ctypes.byref(array), ctypes.byref(changed_pixels), output)

    # Convert the returned value to a Python string
    print("output.value:")
    #print(output.value)
    #print("output.raw:")
    #print(output.raw)
    string_result = output.value.decode()

    # Print the string
    print(string_result)

if __name__ == "__main__":
    create_and_process_array()
