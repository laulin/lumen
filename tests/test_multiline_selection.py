import unittest

import sdl2

from sdl_gui import core
from sdl_gui.primitives.input import Input


class MockContext:
    def measure_text_width(self, text, font, size):
        return len(text) * 10

class TestInputMultilineSelection(unittest.TestCase):

    def setUp(self):
        self.context = MockContext()

    def test_multiline_selection_shift_down(self):
        input_box = Input(0, 0, 100, 100, multiline=True, text="Line1\nLine2")
        input_box.focused = True
        input_box.cursor_pos = 0 # Start of Line 1

        # Shift + Down
        # Should select from 0 to equivalent pos in Line 2.
        # "Line1" len 5. "Line2" len 5.
        # Target index = 6 + 0 = 6.
        # Selection start should become 0. Cursor 6.

        event = {"type": core.EVENT_KEY_DOWN, "key_sym": sdl2.SDLK_DOWN, "mod": sdl2.KMOD_SHIFT}
        input_box.handle_event(event, self.context)

        self.assertEqual(input_box.selection_start, 0)
        self.assertEqual(input_box.cursor_pos, 6) # Start of Line2 (after \n at 5)

    def test_multiline_selection_shift_up(self):
        input_box = Input(0, 0, 100, 100, multiline=True, text="Line1\nLine2")
        input_box.focused = True
        input_box.cursor_pos = 6 # Start of Line 2

        # Shift + Up
        # Should select from 6 to 0.
        event = {"type": core.EVENT_KEY_DOWN, "key_sym": sdl2.SDLK_UP, "mod": sdl2.KMOD_SHIFT}
        input_box.handle_event(event, self.context)

        self.assertEqual(input_box.selection_start, 6)
        self.assertEqual(input_box.cursor_pos, 0)

if __name__ == '__main__':
    unittest.main()
