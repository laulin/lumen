import unittest
from sdl_gui.layouts.hbox import HBox
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui import core

class TestHBox(unittest.TestCase):
    def test_hbox_structure(self):
        """Test HBox data generation."""
        hbox = HBox(x=0, y=0, width="100%", height="100%")
        rect1 = Rectangle(x=0, y=0, width=50, height="100%", color=(255, 0, 0, 255))
        
        hbox.add_child(rect1)
        
        data = hbox.to_data()
        
        self.assertEqual(data[core.KEY_TYPE], core.TYPE_HBOX)
        self.assertEqual(len(data[core.KEY_CHILDREN]), 1)
