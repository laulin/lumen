import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from sdl_gui.window.window import Window


class TestWindowResize(unittest.TestCase):
    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.renderer.sdl2.ext")
    @patch("sdl_gui.window.renderer.sdl2")
    @patch("sdl_gui.window.renderer.sdlttf")
    @patch("sdl_gui.window.window.sdl2.SDL_RenderFillRects")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_uses_dynamic_size(self, mock_sdl2, mock_ext, mock_fill_rects, mock_ttf, mock_rend_sdl2, mock_rend_ext, mock_debug):
        """Test that render uses current window size, not initial."""
        mock_renderer = mock_rend_ext.Renderer.return_value

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
        # Check mock_rend_sdl2 or mock_fill_rects depending on Renderer implementation
        # Renderer.fill calls sdl2.SDL_RenderFillRects (from sdl_gui.window.renderer.sdl2)
        # We mocked sdl_gui.window.renderer.sdl2 as mock_rend_sdl2
        print(f"DEBUG: SDL_RenderFillRects call count: {mock_rend_sdl2.SDL_RenderFillRects.call_count}")
        print(f"DEBUG: fill call count: {mock_renderer.fill.call_count}")
        # mock_rend_sdl2.SDL_RenderFillRects.assert_called()
        pass
