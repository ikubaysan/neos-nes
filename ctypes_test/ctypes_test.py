import numpy as np
import ctypes

# Load the shared library
mylib = ctypes.CDLL('./mylib.so', winmode=0)

# Define the function prototype
class Array3D(ctypes.Structure):
    _fields_ = [
        ("shape", ctypes.c_int * 3),
        ("data", ctypes.POINTER(ctypes.c_ubyte)),
    ]

process_array = mylib.process_array
process_array.argtypes = [ctypes.POINTER(Array3D)]
process_array.restype = ctypes.c_char_p

# Create a 3D ndarray
state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)

# Convert the ndarray to a C-compatible structure
array = Array3D((state.shape[0], state.shape[1], state.shape[2]), state.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)))

# Call the C++ function
result = process_array(ctypes.byref(array))

# Convert the returned value to a Python string
string_result = result.decode()

# Print the string
print(string_result)
