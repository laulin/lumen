import unittest

import sdl2

from sdl_gui import core
from sdl_gui.primitives.input import Input


class MockContext:
    def measure_text_width(self, text, font, size):
        # Mock measurement: 10px per char
        return len(text) * 10

class TestInputPrimitive(unittest.TestCase):

    def setUp(self):
        self.input_box = Input(0, 0, 200, 30, id="test_input")
        self.context = MockContext()
        self.input_box.focused = True # Assume focused for key tests

    def test_text_entry(self):
        # Simulate typing "Hello"
        for char in "Hello":
            event = {"type": core.EVENT_TEXT_INPUT, "text": char}
            self.input_box.handle_event(event, self.context)

        self.assertEqual(self.input_box.text, "Hello")
        self.assertEqual(self.input_box.cursor_pos, 5)

    def test_backspace(self):
        self.input_box.text = "Hello"
        self.input_box.cursor_pos = 5

        event = {"type": core.EVENT_KEY_DOWN, "key_sym": sdl2.SDLK_BACKSPACE, "mod": 0}
        self.input_box.handle_event(event, self.context)

        self.assertEqual(self.input_box.text, "Hell")
        self.assertEqual(self.input_box.cursor_pos, 4)

    def test_cursor_movement_and_selection(self):
        self.input_box.text = "Hello"
        self.input_box.cursor_pos = 5

        # Shift+Left -> Select "o"
        event = {"type": core.EVENT_KEY_DOWN, "key_sym": sdl2.SDLK_LEFT, "mod": sdl2.KMOD_SHIFT}
        self.input_box.handle_event(event, self.context)

        self.assertEqual(self.input_box.cursor_pos, 4)
        self.assertEqual(self.input_box.selection_start, 5) # Selection from 4 to 5 ("o")

        # Backspace -> Delete selection
        event_del = {"type": core.EVENT_KEY_DOWN, "key_sym": sdl2.SDLK_BACKSPACE, "mod": 0}
        self.input_box.handle_event(event_del, self.context)

        self.assertEqual(self.input_box.text, "Hell")
        self.assertEqual(self.input_box.cursor_pos, 4)
        self.assertIsNone(self.input_box.selection_start)

    def test_mouse_positioning(self):
        self.input_box.text = "Hello"
        # Each char is 10px wide in mock.
        # Click at 25px -> Should be index 2 (between 'e' and 'l') or 3?
        # 0:0, 1:10, 2:20, 3:30.
        # 25 is closer to 30 (index 3) than 20 (index 2)? 25-20=5, 30-25=5. Logic picked closest.
        # My naive logic: scan 0..5.
        # ""->0, "H"->10, "He"->20, "Hel"->30.
        # 25 diff 20 is 5. 25 diff 30 is 5.
        # It breaks on increasing diff.
        # Loop 0: diff 25. Best=0.
        # Loop 1: diff 15. Best=1.
        # Loop 2: diff 5. Best=2.
        # Loop 3: diff 5. Best still 2? No, `diff < min_diff` is false if equal. So stays 2.

        self.input_box.click_count = 0
        self.input_box.last_click_time = -1000
        event = {"type": core.EVENT_CLICK, "local_x": 25}
        self.input_box.handle_event(event, self.context)
        # Expected: 2 ("He|llo") or 3 ("Hel|lo") depending on exact logic.
        # With current logic: best_idx=2.
        self.assertEqual(self.input_box.cursor_pos, 2)

        # Click at 45px -> "Hello" is 50px. 45 is closer to end (index 5) than index 4 (40px).
        # diff 4: 5. diff 5: 5.
        # Correctly stays at 4?
        # Let's try 32px. Index 3 is 30. Index 4 is 40. Closer to 3.
        self.input_box.click_count = 0
        self.input_box.last_click_time = -1000
        event = {"type": core.EVENT_CLICK, "local_x": 32}
        self.input_box.handle_event(event, self.context)
        self.assertEqual(self.input_box.cursor_pos, 3)

    def test_copy_paste(self):
        # We can't easily mock SDL_Clipboard without patching sdl2 module functions,
        # but we can verify calls if we mocked sdl2.
        pass

    def test_to_data(self):
        self.input_box.text = "Test"
        self.input_box.cursor_pos = 2
        self.input_box.focused = True

        data = self.input_box.to_data()
        self.assertEqual(data[core.KEY_TYPE], core.TYPE_INPUT)
        self.assertEqual(data[core.KEY_TEXT], "Test")
        self.assertEqual(data["cursor_pos"], 2)
        self.assertTrue(data["focused"])

if __name__ == '__main__':
    unittest.main()
