# distutils: language = c++
# cython: language_level=3

import numpy as np
cimport numpy as np
from libc.stdint cimport uint8_t

def _frame_to_string_common(np.ndarray[uint8_t, ndim=3] frame, np.ndarray[np.npy_bool, ndim=1] changed_pixels = None):
    cdef str last_color = None
    cdef int same_color_start = -1
    cdef str message = ""
    cdef int total_pixels = frame.shape[0] * frame.shape[1]

    # Flatten the frame for simpler iteration
    cdef np.ndarray[uint8_t, ndim=2] frame_copy = frame.reshape(-1, 3)

    # If changed_pixels is None, consider all pixels as changed
    if changed_pixels is None:
        changed_pixels = np.ones(total_pixels, dtype=bool)
    else:
        changed_pixels = changed_pixels.reshape(-1)

    # cdef variables for inside loop
    cdef int r, g, b, rgb_int
    cdef np.ndarray[uint8_t, ndim=1] pixel
    cdef bint changed

    # Iterate over pixels that changed
    for i in range(total_pixels):
        pixel = frame_copy[i]
        changed = changed_pixels[i]

        # Take an RGB tuple and convert it into a single UTF-32 character
        r = pixel[0] >> 2
        g = pixel[1] >> 2
        b = pixel[2] >> 2

        rgb_int = (b << 10) | (g << 5) | r  # Swap red and blue channels

        # Adjust if in the Unicode surrogate range
        if 0xD800 <= rgb_int <= 0xDFFF:
            print("Avoiding Unicode surrogate range")
            if rgb_int < 0xDC00:
                rgb_int = 0xD7FF  # Maximum value just before the surrogate range
            else:
                rgb_int = 0xE000  # Minimum value just after the surrogate range

        color = chr(rgb_int)

        if changed and color != last_color:
            if last_color is not None and same_color_start != -1:
                message += f"{same_color_start}+{i - 1 - same_color_start}_{last_color}"
            same_color_start = i
            last_color = color
        elif not changed and same_color_start != -1:
            message += f"{same_color_start}+{i - 1 - same_color_start}_{last_color}"
            same_color_start = -1
            last_color = None

        if i == total_pixels - 1 and same_color_start != -1:  # the end of the pixels, add the last color
            message += f"{same_color_start}+{i - same_color_start}_{last_color}"

    return message
