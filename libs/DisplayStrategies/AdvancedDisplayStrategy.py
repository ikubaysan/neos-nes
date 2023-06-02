from libs.DisplayStrategies.DisplayStrategy import *

class AdvancedDisplayStrategy(DisplayStrategy):
    def __init__(self, host: str, port: int, scale_percentage: int):
        super().__init__(host=host, port=port, scale_percentage=scale_percentage)

    def display(self):
        return self.show_frame('NES Emulator Frame Viewer (Canvas)')

    def update_canvas(self, message: str, canvas=None, display_canvas_every_update: bool=False):
        update_canvas(message=message,
                      canvas=canvas if canvas is not None else self.canvas,
                      offset=OFFSET,
                      display_canvas_every_update=display_canvas_every_update
                      )