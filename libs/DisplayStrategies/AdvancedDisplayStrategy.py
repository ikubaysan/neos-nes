from Helpers.GeneralHelpers import *
from libs.DisplayStrategies.DisplayStrategy import *

class AdvancedDisplayStrategy(DisplayStrategy):
    OFFSET = 3
    def __init__(self, host: str, port: int, scale_percentage: int):
        super().__init__(host=host, port=port, scale_percentage=scale_percentage)

    def update_canvas(self, message: str):
        i = 0
        while i < len(message):
            row = ord(message[i]) - self.OFFSET  # Get the row index
            i += 1
            color = utf8_to_rgb(message[i], offset=self.OFFSET)  # Convert the UTF-8 character to RGB
            i += 1
            while i < len(message):  # Check for delimiter A (end of color)
                if message[i] == '\x01':
                    # If we've reached delimiter A, we're done applying this color to ranges of columns in the current row.
                    i += 1
                    if message[i] == '\x02':
                        # If we've reached delimiter B, there are no more colors for this row.
                        break
                    else:
                        # Otherwise, the next character represents a new color.
                        color = utf8_to_rgb(message[i], offset=self.OFFSET)  # Convert the UTF-8 character to RGB
                        i += 1

                while i + 1 < len(message) and message[i] != '\x01':  # Check for delimiters A and B
                    start = ord(message[i]) - self.OFFSET  # Get the start index of the range
                    i += 1
                    range_length = ord(message[i]) - self.OFFSET  # Get the length of the range
                    for j in range(start, start + range_length + 1):
                        # While the intuitive access might be self.canvas[row][j], we are using self.canvas[j][row] because
                        # in our case, the j refers to the column of the canvas and row refers to the row.
                        self.canvas[j][row] = color  # Update the canvas with the color for each index in the range
                    i += 1
            i += 1
        return


    def display(self):
        return self.show_frame('NES Emulator Frame Viewer (Canvas)')