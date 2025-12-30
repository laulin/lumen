import unittest
from unittest.mock import MagicMock, patch
from sdl_gui.window.window import Window
from sdl_gui import core

class TestWindowLayout(unittest.TestCase):
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_vbox_layout(self, mock_sdl2, mock_ext):
        """Test vertical stacking of VBox children."""
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        
        win = Window("Test", 100, 300)
        
        # VBox at (0,0) with size 100x300
        # Child 1: Height 50 -> should be at y=0, h=50
        # Child 2: Height 50 -> should be at y=50, h=50
        display_list = [
            {
                "type": "vbox",
                "rect": [0, 0, 100, 300],
                "padding": (0,0,0,0), "margin": (0,0,0,0),
                "children": [
                    { "type": "rect", "rect": [0, 0, 50, 50], "color": (255,0,0,255), "padding": (0,0,0,0), "margin": (0,0,0,0) },
                    { "type": "rect", "rect": [0, 0, 50, 50], "color": (0,255,0,255), "padding": (0,0,0,0), "margin": (0,0,0,0) }
                ]
            }
        ]
        
        win.render(display_list)
        
        # Check calls to fill
        # We expect 2 calls.
        # Call 1: rect=(0, 0, 50, 50)
        # Call 2: rect=(0, 50, 50, 50)  <-- Stacked vertically!
        
        calls = mock_renderer.fill.call_args_list
        self.assertEqual(len(calls), 2)
        
        rect1 = calls[0][0][0]
        rect2 = calls[1][0][0]
        
        self.assertEqual(rect1, (0, 0, 50, 50))
        self.assertEqual(rect2, (0, 50, 50, 50))

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_vbox_padding_margin(self, mock_sdl2, mock_ext):
        """Test VBox padding and child margins."""
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        
        win = Window("Test", 100, 300)
        
        # VBox padding: 10
        # Child 1 margin: 5
        # Start Y = VBox.y + PaddingTop (10) + MarginTop (5) = 15
        display_list = [
            {
                "type": "vbox",
                "rect": [0, 0, 100, 300],
                "padding": (10, 10, 10, 10), "margin": (0,0,0,0),
                "children": [
                    { "type": "rect", "rect": [0, 0, 50, 50], "color": (255,0,0,255), "padding": (0,0,0,0), "margin": (5,5,5,5) }
                ]
            }
        ]
        
        win.render(display_list)
        
        calls = mock_renderer.fill.call_args_list
        rect1 = calls[0][0][0]
        
        # Expected X: VBox.x + PaddingLeft(10) + MarginLeft(5) = 15
        # Expected Y: VBox.y + PaddingTop(10) + MarginTop(5) = 15
        self.assertEqual(rect1, (15, 15, 50, 50))
