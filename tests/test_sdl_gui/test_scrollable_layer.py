import unittest
from unittest.mock import MagicMock
from sdl_gui.layers.scrollable_layer import ScrollableLayer
from sdl_gui import core

class TestScrollableLayer(unittest.TestCase):
    def test_init(self):
        layer = ScrollableLayer(0, 0, 100, 100, scroll_y=50, content_height=500, id="test_scroll")
        data = layer.to_data()
        
        self.assertEqual(data[core.KEY_TYPE], core.TYPE_SCROLLABLE_LAYER)
        self.assertEqual(data[core.KEY_SCROLL_Y], 50)
        self.assertEqual(data[core.KEY_CONTENT_HEIGHT], 500)
        self.assertEqual(data[core.KEY_ID], "test_scroll")
        
    def test_scroll_state(self):
        layer = ScrollableLayer(0,0,100,100)
        layer.scroll_y = 100
        data = layer.to_data()
        self.assertEqual(data[core.KEY_SCROLL_Y], 100)
