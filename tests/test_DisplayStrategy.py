import pytest
import numpy as np
import random
import time
from Helpers.GeneralHelpers import *
from libs.DisplayStrategies.AdvancedDisplayStrategy import *

HOST = '10.0.0.147'
PORT = 9001

@pytest.fixture
def advanced_display_strategy():
    display_strategy = AdvancedDisplayStrategy(host=HOST, port=PORT, scale_percentage=100)
    return display_strategy

def test_update_canvas_1(advanced_display_strategy: AdvancedDisplayStrategy):
    OFFSET = advanced_display_strategy.OFFSET

    delim_a = chr(1) # end of color
    delim_b = chr(2) # end of row

    message = ""

    # row 0
    message += chr(0 + OFFSET)
    # color 0
    message += rgb_to_utf32(r=12, g=5, b=50)

    # range 0 column start
    message += chr(3 + OFFSET)
    # range 0 span
    message += chr(5 + OFFSET)

    # range 1 column start
    message += chr(13 + OFFSET)
    # range 1 span
    message += chr(5 + OFFSET)

    # delim a
    message += delim_a

    # Done applying color 0 to this row. Are there any other colors?
    # yes.
    # color 1
    message += rgb_to_utf32(r=120, g=50, b=250)
    # range 0 column start
    message += chr(23 + OFFSET)
    # range 0 span
    message += chr(5 + OFFSET)

    # range 1 column start
    message += chr(33 + OFFSET)
    # range 1 span
    message += chr(5 + OFFSET)

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

    for row in range(FRAME_HEIGHT):
        # Append row
        message += chr(row + OFFSET)

        # Randomly select the number of colors for this row
        num_colors = random.randint(1, 5)

        for _ in range(num_colors):
            # Randomly select RGB values
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)

            # Append color
            message += rgb_to_utf32(r, g, b)

            # Randomly select the number of color ranges for this color
            num_ranges = random.randint(1, 5)

            for _ in range(num_ranges):
                # Randomly select start of color range
                start = random.randint(0, FRAME_WIDTH - 1)

                # Randomly select range span. It must not exceed the amount of columns from the start
                span = random.randint(1, FRAME_WIDTH - start)

                # Append range start and span
                message += chr(start + OFFSET)
                message += chr(span + OFFSET)

            # Append end of color delimiter
            message += delim_a

        # Append end of row delimiter
        message += delim_b

    # Update and display canvas
    print(message)
    advanced_display_strategy.update_canvas(message=message)
    advanced_display_strategy.display()
    time.sleep(5)
    return


def test_rgb_utf32_conversion():
    # Test case 1: Red color
    r = 255
    g = 0
    b = 0
    utf32_char = rgb_to_utf32(r, g, b)
    rgb_tuple = utf32_to_rgb(utf32_char)

    # Test case 2: Green color
    r = 0
    g = 255
    b = 0
    utf32_char = rgb_to_utf32(r, g, b)
    rgb_tuple = utf32_to_rgb(utf32_char)

    # Test case 3: Blue color
    r = 0
    g = 0
    b = 255
    utf32_char = rgb_to_utf32(r, g, b)
    rgb_tuple = utf32_to_rgb(utf32_char)


    # Test case 4: Custom color
    r = 128
    g = 64
    b = 192
    utf32_char = rgb_to_utf32(r, g, b)
    rgb_tuple = utf32_to_rgb(utf32_char)
    return


def test_unicode_utf32_conversion():
    # Convert Unicode codepoint to UTF-32 char
    codepoint1 = 990
    utf32_char = chr(codepoint1)
    print(utf32_char)  # Output: Ϟ

    # Convert UTF-32 char to Unicode codepoint
    utf32_char = "Ϟ"
    codepoint2 = ord(utf32_char)
    print(codepoint2)  # Output: 990
    assert codepoint1 == codepoint2