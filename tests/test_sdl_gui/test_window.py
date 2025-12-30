import unittest
from unittest.mock import MagicMock, patch
from sdl_gui.window.window import Window
from sdl_gui import core

class TestWindow(unittest.TestCase):
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_window_init(self, mock_sdl2, mock_ext):
        """Test window initialization calls SDL functions."""
        win = Window("Test", 800, 600)
        mock_ext.init.assert_called_once()
        mock_ext.Window.assert_called_with("Test", size=(800, 600), flags=mock_sdl2.SDL_WINDOW_RESIZABLE)
        
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_dispatch(self, mock_sdl2, mock_ext):
        """Test that render method dispatches to correct drawers."""
        # Setup mocks
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        
        win = Window("Test", 800, 600)
        
        # Test data
        display_list = [
            {
                "type": "layer",
                "rect": [0, 0, 800, 600],
                "children": [
                    { "type": "rect", "rect": [10, 10, 50, 50], "color": (255, 0, 0, 255) }
                ]
            }
        ]
        
        win.render(display_list)
        
        # Verify renderer calls
        # clear called
        mock_renderer.clear.assert_called()
        # present called
        mock_renderer.present.assert_called()
        # fill called for rect (layer doesn't draw itself usually, but its children do)
        # Note: Implementation details of drawing might vary, assuming fill() for rect
        mock_renderer.fill.assert_called() 

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_percentages(self, mock_sdl2, mock_ext):
        """Test that percentages are resolved to pixels."""
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        
        # Window size 800x600
        win = Window("Test", 800, 600)
        
        display_list = [
            {
                "type": "rect",
                "rect": ["10%", "50%", "50%", "25%"], # x=80, y=300, w=400, h=150
                "color": (255, 0, 0, 255)
            }
        ]
        
        win.render(display_list)
        
        # Check that fill was called with resolved integers
        # Expected rect: (80, 300, 400, 150)
        args, _ = mock_renderer.fill.call_args
        resolved_rect = args[0]
        
        self.assertEqual(resolved_rect, (80, 300, 400, 150))
 
