from libs.Helpers.GeneralHelpers import *


class MessageViewer:
    def __init__(self, messages, display_strategy, cycle_mode=False, start_index=0, end_index=-1, window_name=""):
        self.messages = messages
        self.display_strategy = display_strategy
        self.end_index = end_index if end_index != -1 else len(messages) - 1
        self.start_index = start_index
        self.index = start_index
        self.previous_index = -1
        self.cycle_mode = cycle_mode
        self.window_name = window_name
        logger.info(f"MessageViewer initialized with {len(self.messages)} messages. Start index: {self.start_index}"
                    f" End index: {self.end_index} Cycle mode: {self.cycle_mode}")

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
        elif key == 'KEY_LEFT' and not self.cycle_mode:
            self.index = max(0, self.index - 1)
        elif key == 'KEY_RIGHT':
            if self.cycle_mode and self.index + 1 >= self.end_index:
                # If we are at the end of the list, go back to the start
                    self.index = self.start_index
                    logger.info(f"Cycle mode: Reset index to {self.index} after reaching end of list (index {self.end_index})")
            else:
                self.index = min(len(self.messages) - 1, self.index + 1)

        return True

    def start(self):
        while self.handle_input():
            self.display_message()
