import unittest

from sdl_gui import core
from sdl_gui.layouts.vbox import VBox
from sdl_gui.primitives.rectangle import Rectangle


class TestVBox(unittest.TestCase):
    def test_vbox_structure(self):
        """Test VBox data generation."""
        vbox = VBox(x=0, y=0, width="100%", height="100%", padding=(10, 10, 10, 10))
        rect1 = Rectangle(x=0, y=0, width="100%", height=50, color=(255, 0, 0, 255))
        rect2 = Rectangle(x=0, y=0, width="100%", height=50, color=(0, 255, 0, 255))

        vbox.add_child(rect1)
        vbox.add_child(rect2)

        data = vbox.to_data()

        self.assertEqual(data[core.KEY_TYPE], core.TYPE_VBOX)
        self.assertEqual(data[core.KEY_PADDING], (10, 10, 10, 10))
        self.assertEqual(len(data[core.KEY_CHILDREN]), 2)
