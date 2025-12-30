import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from sdl_gui.window.window import Window
from sdl_gui import core

class TestWindowResize(unittest.TestCase):
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_uses_dynamic_size(self, mock_sdl2, mock_ext):
        """Test that render uses current window size, not initial."""
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        
        # Mock window instance
        mock_window_instance = MagicMock()
        mock_ext.Window.return_value = mock_window_instance
        
        # Initial size 800x600
        win = Window("Test", 800, 600)
        
        # SIMULATE RESIZE: Change window.size return value to 1024x768
        type(mock_window_instance).size = PropertyMock(return_value=(1024, 768))
        
        # Layer that fills 100%
        display_list = [
            {
                "type": "rect",
                "rect": ["0%", "0%", "100%", "100%"], 
                "color": (0,0,0,0)
            }
        ]
        
        win.render(display_list)
        
        # Check that fill was called with resized dimensions (1024, 768)
        # NOT (800, 600)
        
        args, _ = mock_renderer.fill.call_args
        resolved_rect = args[0]
        
        self.assertEqual(resolved_rect, (0, 0, 1024, 768))
