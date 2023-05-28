import numpy as np

from Helpers.GeneralHelpers import *
from libs.DisplayStrategies.DisplayStrategy import *

class AdvancedDisplayStrategy(DisplayStrategy):
    OFFSET = 16
    def __init__(self, host: str, port: int, scale_percentage: int):
        super().__init__(host=host, port=port, scale_percentage=scale_percentage)

    def display(self):
        return self.show_frame('NES Emulator Frame Viewer (Canvas)')

    def update_canvas(self, message: str, canvas=None):
        update_canvas(message=message,
                      canvas=canvas if canvas is not None else self.canvas,
                      offset=self.OFFSET)