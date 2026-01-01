import unittest

from sdl_gui import core
from sdl_gui.primitives.rectangle import Rectangle


class TestRectangle(unittest.TestCase):
    def test_rectangle_to_data(self):
        """Test that Rectangle generates correct display list data."""
        rect = Rectangle(x=10, y=20, width=100, height=200, color=(255, 0, 0, 255))
        data = rect.to_data()

        self.assertEqual(data[core.KEY_TYPE], core.TYPE_RECT)
        self.assertEqual(data[core.KEY_RECT], [10, 20, 100, 200])
        self.assertEqual(data["color"], (255, 0, 0, 255))
