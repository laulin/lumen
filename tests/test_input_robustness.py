import unittest

from sdl_gui.primitives.input import Input


class MockContext:
    def measure_text_width(self, text, font, size):
        return len(text) * 10

class TestInputRobustness(unittest.TestCase):

    def setUp(self):
        self.context = MockContext()

    def test_mouse_click_with_scroll(self):
        # Single line input, scrolled 50px
        input_box = Input(0, 0, 100, 30)
        input_box.text = "0123456789" # 100px width
        input_box.scroll_x = 20 # Scrolled such that "01" are hidden. Viual start is "2".

        # Click at local_x = 10.
        # effective_x = 10 + 20 = 30.
        # "012" is 30px width. So index 3? Or 3 chars "012".
        # measure("012") = 30.
        # Should set cursor to 3.

        input_box._set_cursor_from_mouse(10, 0, self.context)
        self.assertEqual(input_box.cursor_pos, 3)

    def test_mouse_click_multiline(self):
        # Multiline. Line height approx 20 (16+4)
        input_box = Input(0, 0, 100, 100, multiline=True, size=16)
        input_box.text = "Line0\nLine1\nLine2"
        input_box.scroll_y = 10 # Scrolled 10px down.

        # Click at local_y = 40.
        # effective_y = 40 + 10 = 50.
        # Padding 5. rel_y = 45.
        # Line 0: 0-20. Line 1: 20-40. Line 2: 40-60.
        # 45 is inside Line 2.

        input_box._set_cursor_from_mouse(10, 40, self.context)
        self.assertEqual(input_box.cursor_pos, 13)

if __name__ == '__main__':
    unittest.main()
