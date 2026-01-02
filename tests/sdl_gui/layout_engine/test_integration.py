import unittest
from unittest.mock import MagicMock
from sdl_gui import core
from sdl_gui.window.renderer import Renderer
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.rectangle import Rectangle

class TestFlexboxIntegration(unittest.TestCase):
    def setUp(self):
        # Mock Window/SDL components usually, but Renderer needs integration.
        # We can subclass Renderer or mock the SDL parts.
        pass

    def test_renderer_measure_flexbox_auto_height(self):
        """
        Verify that Renderer._measure_flexbox_height correctly returns the height
        of a FlexBox with height='auto' based on its children.
        """
        # Patching sdl2.ext.Renderer to avoid creation issues
        with unittest.mock.patch('sdl2.ext.Renderer') as MockRenderer:
            renderer = Renderer(window=MagicMock(), flags=0)
        
        # Manually setup mocks needed by measure
        # measure typically doesn't call SDL drawing, just logic.
        
        # Create a Column with 2 children of height 50 each.
        # The container has height='auto'.
        container = FlexBox(
            x=0, y=0, width=200, height="auto",
            flex_direction="column",
            padding=(0,0,0,0),
            gap=0
        )
        c1 = Rectangle(x=0,y=0,width=100,height=50, color=(0,0,0,0)) # Normal rect
        c2 = Rectangle(x=0,y=0,width=100,height=50, color=(0,0,0,0))
        container.add_child(c1)
        container.add_child(c2)
        
        item_data = container.to_data()
        
        # Measure
        # Available width 200, height infinite/large?
        h = renderer._measure_flexbox_height(item_data, 200, 1000)
        
        # Should be 100
        self.assertEqual(h, 100, "Flexbox column should sum children heights when auto")

    def test_renderer_measure_flexbox_row_auto_height(self):
        """Test row height is max of children."""
        with unittest.mock.patch('sdl2.ext.Renderer') as MockRenderer:
            renderer = Renderer(window=MagicMock(), flags=0)
        
        container = FlexBox(
            x=0, y=0, width=200, height="auto",
            flex_direction="row"
        )
        c1 = Rectangle(x=0,y=0,width=50,height=40, color=(0,0,0,0))
        c2 = Rectangle(x=0,y=0,width=50,height=60, color=(0,0,0,0)) # Max height
        container.add_child(c1)
        container.add_child(c2)
        
        item_data = container.to_data()
        h = renderer._measure_flexbox_height(item_data, 200, 1000)
        
        self.assertEqual(h, 60, "Flexbox row height should be max child height")

    def test_normalize_box_model(self):
        """Test conversion of various inputs to 4-tuples."""
        with unittest.mock.patch('sdl2.ext.Renderer'):
             renderer = Renderer(window=MagicMock(), flags=0)
             self.assertEqual(renderer._normalize_box_model(10), (10, 10, 10, 10))
             self.assertEqual(renderer._normalize_box_model((5, 10)), (5, 10, 5, 10))
             self.assertEqual(renderer._normalize_box_model((1, 2, 3, 4)), (1, 2, 3, 4))
             self.assertEqual(renderer._normalize_box_model("invalid"), (0, 0, 0, 0))

if __name__ == '__main__':
    unittest.main()
