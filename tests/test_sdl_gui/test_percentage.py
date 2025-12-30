import unittest
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.layers.layer import Layer
from sdl_gui import core

class TestPercentageSupport(unittest.TestCase):
    def test_rectangle_accepts_strings(self):
        """Test that Rectangle accepts string dimensions."""
        rect = Rectangle(x="10%", y="10%", width="50%", height="50%", color=(0,0,0,0))
        data = rect.to_data()
        self.assertEqual(data[core.KEY_RECT], ["10%", "10%", "50%", "50%"])

    def test_layer_accepts_strings(self):
        """Test that Layer accepts string dimensions."""
        layer = Layer(x="0%", y="0%", width="100%", height="100%")
        data = layer.to_data()
        self.assertEqual(data[core.KEY_RECT], ["0%", "0%", "100%", "100%"])
