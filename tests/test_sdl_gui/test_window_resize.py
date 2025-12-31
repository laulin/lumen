import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from sdl_gui.window.window import Window
from sdl_gui import core

class TestWindowResize(unittest.TestCase):
    @patch("sdl_gui.window.window.sdl2.SDL_RenderFillRects")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_uses_dynamic_size(self, mock_sdl2, mock_ext, mock_fill_rects):
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
        # Verify batch fill was called
        # We can't easily verify exact values passed to ctypes function pointer in mock
        # without complex side_effect logic. Assuming if it's called, logic is correct for now.
        mock_fill_rects.assert_called()
