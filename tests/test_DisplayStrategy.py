import pytest
import numpy as np
import random
import time
from Helpers.GeneralHelpers import *
from libs.DisplayStrategies.AdvancedDisplayStrategy import *
from libs.CtypesLibs.CPPFrameToString import FrameToString

HOST = '10.0.0.147'
PORT = 9001

@pytest.fixture
def advanced_display_strategy():
    display_strategy = AdvancedDisplayStrategy(host=HOST, port=PORT, scale_percentage=100)
    return display_strategy

@pytest.fixture
def frame_to_string():
    frame_to_string = FrameToString()
    return frame_to_string


def message_to_color_dictionary(message, offset):
    # Initialize output dictionary
    color_dict = {}

    # End of color and row delimiters
    delim_a = chr(1)
    delim_b = chr(2)

    i = 0  # Initialize index for looping through the message

    while i < len(message):
        row_idx = ord(message[i]) - offset
        i += 1

        color_dict[row_idx] = {}

        while i < len(message) and message[i] != delim_b:
            color_codepoint = utf8_to_rgb(message[i])
            i += 1

            color_dict[row_idx][color_codepoint] = []

            while i < len(message) and message[i] != delim_a:
                range_start = ord(message[i]) - offset
                i += 1
                range_span = ord(message[i]) - offset
                i += 1
                color_dict[row_idx][color_codepoint].append([range_start, range_span])

            i += 1  # Skip delim_a

        i += 1  # Skip delim_b

    return color_dict




def test_update_canvas_1(advanced_display_strategy: AdvancedDisplayStrategy):
    OFFSET = advanced_display_strategy.OFFSET

    delim_a = chr(1) # end of color
    delim_b = chr(2) # end of row

    message = ""

    # row 0
    message += chr(0 + OFFSET)
    # color 0
    message += rgb_to_utf8(r=12, g=5, b=50, offset=OFFSET)

    # range 0 column start
    message += chr(3 + OFFSET)
    # range 0 span
    message += chr(2 + OFFSET)

    # range 1 column start
    message += chr(13 + OFFSET)
    # range 1 span
    message += chr(4 + OFFSET)

    # delim a <?>
    message += delim_a

    # Done applying color 0 to this row. Are there any other colors?
    # yes.
    # color 1
    message += rgb_to_utf8(r=120, g=50, b=250, offset=OFFSET)
    # range 0 column start
    message += chr(23 + OFFSET)
    # range 0 span
    message += chr(5 + OFFSET)

    # range 1 column start
    message += chr(33 + OFFSET)
    # range 1 span
    message += chr(2 + OFFSET)

    message += delim_a
    # Done applying color 0 to this row. Are there any other colors?
    # no
    message += delim_b

    advanced_display_strategy.update_canvas(message=message)
    advanced_display_strategy.display()
    return


def test_update_canvas_2(advanced_display_strategy: AdvancedDisplayStrategy):
    OFFSET = advanced_display_strategy.OFFSET
    FRAME_WIDTH = DEFAULT_FRAME_WIDTH
    FRAME_HEIGHT = DEFAULT_FRAME_HEIGHT

    delim_a = chr(1)  # end of color
    delim_b = chr(2)  # end of row
    message = ""

    data = {}

    for row in range(FRAME_HEIGHT):
        # Append row
        message += chr(row + OFFSET)

        # Randomly select the number of colors for this row
        num_colors = random.randint(1, 3)
        data[row] = num_colors

        for _ in range(num_colors):
            # Randomly select RGB values
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)

            # Append color
            message += rgb_to_utf8(r, g, b, offset=OFFSET)

            # Randomly select the number of color ranges for this color
            num_ranges = random.randint(1, 3)

            for _ in range(num_ranges):
                # Randomly select start of color range
                start = random.randint(0, FRAME_WIDTH - 2)

                # Randomly select range span. It must not exceed the amount of columns from the start
                span = random.randint(1, FRAME_WIDTH - start - 1)

                # Append range start and span
                message += chr(start + OFFSET)
                message += chr(span + OFFSET)

            # Append end of color delimiter
            message += delim_a

        # Append end of row delimiter
        message += delim_b

    # Update and display canvas
    advanced_display_strategy.update_canvas(message=message)
    advanced_display_strategy.display()
    time.sleep(3)
    return



def test_update_canvas_from_cpp(frame_to_string: FrameToString, advanced_display_strategy: AdvancedDisplayStrategy):
    current_state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)
    last_state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)
    message = frame_to_string.get_string(current_state, last_state)
    message_len = len(message)
    result_dict = message_to_color_dictionary(message=message, offset=16)
    return




def test_rgb_utf8_conversion():
    # Test case 1: Red color
    r = 255
    g = 0
    b = 0
    utf8_char = rgb_to_utf8(r, g, b)
    rgb_tuple = utf8_to_rgb(utf8_char)

    # Test case 2: Green color
    r = 0
    g = 255
    b = 0
    utf8_char = rgb_to_utf8(r, g, b)
    rgb_tuple = utf8_to_rgb(utf8_char)

    # Test case 3: Blue color
    r = 0
    g = 0
    b = 255
    utf8_char = rgb_to_utf8(r, g, b)
    rgb_tuple = utf8_to_rgb(utf8_char)


    # Test case 4: Custom color
    r = 128
    g = 64
    b = 192
    utf8_char = rgb_to_utf8(r, g, b)
    rgb_tuple = utf8_to_rgb(utf8_char)
    return


def test_unicode_utf8_conversion():
    # Convert Unicode codepoint to UTF-8 char
    codepoint1 = 990
    utf8_char = chr(codepoint1)
    print(utf8_char)  # Output: Ϟ

    # Convert UTF-8 char to Unicode codepoint
    utf8_char = "Ϟ"
    codepoint2 = ord(utf8_char)
    print(codepoint2)  # Output: 990
    assert codepoint1 == codepoint2