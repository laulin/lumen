import unittest
from unittest.mock import MagicMock
import sdl2
from sdl_gui.primitives.input import Input
from sdl_gui import core

class MockContext:
    def measure_text_width(self, text, font, size):
        return len(text) * 10

class TestInputCrash(unittest.TestCase):
    
    def setUp(self):
        self.context = MockContext()
        self.input = Input(0, 0, 200, 30, text="Word") # len 4

    def test_double_click_end_of_text_crash(self):
        # Cursor at end (4).
        self.input.cursor_pos = 4
        
        # Double click logic in handle_event calls _select_word_at_cursor
        # which calls _find_prev_word_start(self.cursor_pos + 1) -> 5
        # _find_prev_word_start(5) sets i = 4. text[4] is overflow.
        
        # Trigger via internal method directly to isolate logic
        try:
            self.input._select_word_at_cursor()
        except IndexError:
            self.fail("IndexError raised during _select_word_at_cursor")

if __name__ == '__main__':
    unittest.main()
