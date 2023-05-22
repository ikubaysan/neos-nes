import ctypes

# Load the shared library
mylib = ctypes.CDLL('./mylib.so', winmode=0)

# Define the function prototype
get_string = mylib.get_string
get_string.restype = ctypes.c_char_p

# Call the C++ function
result = get_string()

# Convert the returned value to a Python string
string_result = result.decode()

# Print the string
print(string_result)