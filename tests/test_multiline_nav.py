import unittest
from unittest.mock import MagicMock
import sdl2
from sdl_gui.primitives.input import Input
from sdl_gui import core

class MockContext:
    def measure_text_width(self, text, font, size):
        return len(text) * 10

class TestInputMultilineNav(unittest.TestCase):
    
    def setUp(self):
        self.context = MockContext()

    def test_multiline_nav(self):
        # 3 lines: "Line1\nLine2\nLine3"
        # Lengths with newline: 6, 6, 5
        # Indices: 
        # Line 0: 0-5. (Newline at 5)
        # Line 1: 6-11. (Newline at 11)
        # Line 2: 12-16.
        
        input_box = Input(0, 0, 100, 100, multiline=True, text="Line1\nLine2\nLine3")
        input_box.focused = True
        
        # Cursor at end (17)
        input_box.cursor_pos = len(input_box.text) # 17 ("Line3" is 5 chars. 12+5=17)
        
        # UP -> Should go to end of Line 2 ("Line2" length 5). 
        # Line 2 starts at 6. Col is 5 based on "Line3" length? No.
        # "Line3" is index 12. Cursor 17. Col = 5.
        # Line 2 ("Line2") length 5.
        # Target index = 6 + min(5, 5) = 11. (After '2' in Line2).
        
        event = {"type": core.EVENT_KEY_DOWN, "key_sym": sdl2.SDLK_UP}
        input_box.handle_event(event, self.context)
        self.assertEqual(input_box.cursor_pos, 11)
        
        # UP -> End of Line 1 ("Line1").
        # Col is 5. Line 1 ("Line1") length 5.
        # Target index = 0 + min(5, 5) = 5.
        input_box.handle_event(event, self.context)
        self.assertEqual(input_box.cursor_pos, 5)

    def test_vertical_scroll(self):
        # Height 100. Padding 5+5. Visible 90.
        # Line height approx 20 (16+4).
        input_box = Input(0, 0, 100, 100, multiline=True)
        input_box.focused = True
        
        # Approx 4 lines visible (20*4 = 80 < 90). 5th line might scroll.
        lines = "A\n" * 10
        input_box.text = lines
        
        # Move cursor to end (Line 10).
        input_box.cursor_pos = len(lines)
        
        # Trigger update scroll via dummy key event or manual call
        # Since _update_scroll is internal, we can call handling logic or trigger via key.
        # Let's use down key at end to force update? Or insert.
        # Just insert a char at end.
        input_box._insert_text("B", self.context)
        
        # Cursor is at line 10. y = 10 * 20 = 200.
        # Visible 90.
        # Should scroll to show line 10.
        # scroll_y should be approx 200 - 90 + 20? 
        # Logic: if 200 + 20 > scroll_y + 90.
        self.assertGreater(input_box.scroll_y, 0)
        self.assertLess(input_box.scroll_y, 200)

if __name__ == '__main__':
    unittest.main()
