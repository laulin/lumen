import unittest

from sdl_gui import core
from sdl_gui.primitives.input import Input


class MockContext:
    def measure_text_width(self, text, font, size):
        return len(text) * 10

class TestInputDrag(unittest.TestCase):

    def setUp(self):
        self.context = MockContext()
        self.input = Input(0, 0, 200, 30, text="0123456789")

    def test_drag_selection(self):
        # 1. Click at index 2 (approx 20px)
        evt_down = {"type": core.EVENT_CLICK, "local_x": 20, "local_y": 0}
        self.input.handle_event(evt_down, self.context)

        self.assertTrue(self.input.dragging)
        self.assertEqual(self.input.cursor_pos, 2)
        # Verify anchor set
        # The logic is: if not shift, selection_start = cursor_pos
        self.assertEqual(self.input.selection_start, 2)

        # 2. Drag to index 5 (50px)
        evt_move = {"type": core.EVENT_MOUSE_MOTION, "local_x": 50, "local_y": 0}
        self.input.handle_event(evt_move, self.context)

        # Cursor should move to 5
        self.assertEqual(self.input.cursor_pos, 5)
        # Anchor should STAY at 2
        self.assertEqual(self.input.selection_start, 2)

        # 3. Mouse Up
        self.input.handle_event({"type": core.EVENT_MOUSE_UP, "local_x": 50, "local_y": 0}, self.context)
        self.assertFalse(self.input.dragging)
        # Selection should be [2, 5]
        self.assertEqual(self.input.selection_start, 2)
        self.assertEqual(self.input.cursor_pos, 5)

if __name__ == '__main__':
    unittest.main()
