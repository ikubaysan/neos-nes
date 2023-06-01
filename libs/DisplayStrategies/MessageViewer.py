from libs.Helpers.GeneralHelpers import *


class MessageViewer:
    def __init__(self, messages, display_strategy, window_name=""):
        self.messages = messages
        self.display_strategy = display_strategy
        self.index = 0
        self.previous_index = -1
        self.window_name = window_name

    def display_message(self):
        message = self.messages[self.index]
        self.display_strategy.update_canvas(message=message)
        if self.previous_index != self.index:
            logger.info(f"Displayed frame {self.index}")
        self.previous_index = self.index

    def display(self):
        cv2.imshow("MessageViewer", self.canvas)
        return cv2.waitKey(1) & 0xFF


    def get_key_input(self):
        key_code = self.display()
        if key_code == 27:  # ESC key
            return 'q'
        elif key_code == 81:  # Left arrow key
            return 'KEY_LEFT'
        elif key_code == 83:  # Right arrow key
            return 'KEY_RIGHT'
        else:
            return ''

    def handle_input(self):
        key = self.display_strategy.get_key_input_for_messageviewer(window_name=self.window_name)
        if key == 'q':
            return False
        elif key == 'KEY_LEFT':
            self.index = max(0, self.index - 1)
        elif key == 'KEY_RIGHT':
            self.index = min(len(self.messages) - 1, self.index + 1)
        return True

    def start(self):
        while self.handle_input():
            self.display_message()
