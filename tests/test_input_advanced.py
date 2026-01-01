import unittest

import sdl2

from sdl_gui import core
from sdl_gui.primitives.input import Input


class MockContext:
    def measure_text_width(self, text, font, size):
        # Mock measurement: 10px per char
        return len(text) * 10

class TestInputAdvanced(unittest.TestCase):

    def setUp(self):
        self.context = MockContext()

    def test_max_length(self):
        # Input with max_length=5
        input_box = Input(0, 0, 200, 30, max_length=5, id="test_limit")
        input_box.focused = True

        # Try to type 6 chars
        input_box._insert_text("123456", self.context)

        self.assertEqual(input_box.text, "12345")
        self.assertEqual(len(input_box.text), 5)

        # Try appending more
        input_box._insert_text("A", self.context)
        self.assertEqual(input_box.text, "12345")

    def test_scroll_logic(self):
        # Width 60. Padding 10 (5+5). Visible 50.
        # Each char 10px. 5 chars fill input.
        input_box = Input(0, 0, 60, 30, padding=(0,5,0,5))
        input_box.focused = True

        # Type "ABCDE" (50px). Should fit exactly or close.
        input_box._insert_text("ABCDE", self.context) # 50px
        # Cursor at 50. Visible Width 50 (60-10).
        # Logic: 50 <= 0 + 50. Scroll stays 0?
        # Let's see: `if cursor_px (50) > scroll_x (0) + visible (50)` -> False (Equal).
        self.assertEqual(input_box.scroll_x, 0)

        # Type "F". 60px.
        input_box._insert_text("F", self.context)
        # Cursor 60. > 0 + 50.
        # scroll_x = 60 - 50 = 10.
        self.assertEqual(input_box.scroll_x, 10)

        # Move Left (cursor 50).
        # 50 < 10 ? False.
        # 50 > 10 + 50 (60)? False.
        # Scroll stays 10? Yes. Text "BCDEF" visible.
        event = {"type": core.EVENT_KEY_DOWN, "key_sym": sdl2.SDLK_LEFT, "mod": 0}
        input_box.handle_event(event, self.context)
        self.assertEqual(input_box.cursor_pos, 5)
        self.assertEqual(input_box.scroll_x, 10)

        # Move Home
        event["key_sym"] = sdl2.SDLK_HOME
        input_box.handle_event(event, self.context)
        # Cursor 0. 0 < 10 -> True. Scroll -> 0.
        self.assertEqual(input_box.scroll_x, 0)

    def test_multiline_insert(self):
        input_box = Input(0, 0, 200, 100, multiline=True)
        input_box.focused = True

        # Enter key
        event = {"type": core.EVENT_KEY_DOWN, "key_sym": sdl2.SDLK_RETURN, "mod": 0}
        input_box.handle_event(event, self.context)

        self.assertEqual(input_box.text, "\n")

        # Non-multiline should submit instead
        input_box_single = Input(0, 0, 200, 30, multiline=False)
        input_box_single.focused = True
        submitted = False
        def on_sub(t): nonlocal submitted; submitted = True
        input_box_single.on_submit = on_sub

        input_box_single.handle_event(event, self.context)
        self.assertEqual(input_box_single.text, "")
        self.assertTrue(submitted)

if __name__ == '__main__':
    unittest.main()
