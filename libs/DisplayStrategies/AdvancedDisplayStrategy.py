from Helpers.GeneralHelpers import *
from libs.DisplayStrategies.DisplayStrategy import *

class AdvancedDisplayStrategy(DisplayStrategy):
    OFFSET = 2
    def __init__(self, host: str, port: int, scale_percentage: int):
        super().__init__(host=host, port=port, scale_percentage=scale_percentage)

    def update_canvas(self, message: str):
        i = 0
        message_len = len(message)
        while i < len(message):
            # TODO: row starts at 0 as it should, but doesn't consistently increase. why?
            row = ord(message[i]) - self.OFFSET  # Get the row index
            i += 1
            while i < len(message) and message[i] != '\x01':  # Check for delimiter A (end of color)
                color = utf32_to_rgb(message[i], offset=self.OFFSET)  # Convert the UTF-32 character to RGB
                i += 1
                while i + 1 < len(message) and message[i] not in ('\x01', '\x02'):  # Check for delimiters A and B
                    start = ord(message[i]) - self.OFFSET  # Get the start index of the range
                    i += 1
                    range_length = ord(message[i]) - self.OFFSET  # Get the length of the range
                    i += 1
                    for j in range(start, start + range_length + 1):
                        # why?
                        if j >= len(self.canvas[row]):
                            break
                        self.canvas[row][j] = color  # Update the canvas with the color for each index in the range
                if i < len(message) and message[i] == '\x02':  # Check for delimiter B (end of row)
                    break
                i += 1
            i += 1
        return

    def display(self):
        return self.show_frame('NES Emulator Frame Viewer (Canvas)')