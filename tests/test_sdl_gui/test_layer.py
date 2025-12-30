import unittest
from sdl_gui.layers.layer import Layer
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui import core

class TestLayer(unittest.TestCase):
    def test_layer_structure(self):
        """Test layer data generation with children."""
        layer = Layer(x=0, y=0, width=800, height=600)
        rect = Rectangle(10, 10, 50, 50, (255, 0, 0, 255))
        
        layer.add_child(rect)
        
        data = layer.to_data()
        
        self.assertEqual(data[core.KEY_TYPE], core.TYPE_LAYER)
        self.assertEqual(data[core.KEY_RECT], [0, 0, 800, 600])
        self.assertEqual(len(data[core.KEY_CHILDREN]), 1)
        self.assertEqual(data[core.KEY_CHILDREN][0][core.KEY_TYPE], core.TYPE_RECT)
