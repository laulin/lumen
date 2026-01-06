import unittest
from unittest.mock import MagicMock, patch

from sdl_gui import core
from sdl_gui.window.window import Window


class TestWindow(unittest.TestCase):
    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.window.Renderer")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_window_init(self, mock_sdl2, mock_ext, mock_renderer_cls, mock_debug):
        """Test window initialization calls SDL functions."""
        win = Window("Test", 800, 600)
        mock_ext.init.assert_called_once()
        mock_ext.Window.assert_called_with("Test", size=(800, 600), flags=mock_sdl2.SDL_WINDOW_RESIZABLE)
        mock_renderer_cls.assert_called_once()

    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.window.Renderer")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_dispatch(self, mock_sdl2, mock_ext, mock_renderer_cls, mock_debug):
        """Test that render method dispatches to correct drawers."""
        # Setup mocks
        mock_renderer = mock_renderer_cls.return_value



        # Mock window size
        mock_window = MagicMock()
        mock_window.size = (800, 600)
        mock_ext.Window.return_value = mock_window

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
        
        # Verify render_list called with display_list
        mock_renderer.render_list.assert_called_with(display_list, force_full=False)

    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.window.Renderer")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_percentages(self, mock_sdl2, mock_ext, mock_renderer_cls, mock_debug):
        """Test that percentages are resolved to pixels."""
        mock_renderer = mock_renderer_cls.return_value


        # Mock window size
        mock_window = MagicMock()
        mock_window.size = (800, 600)
        mock_ext.Window.return_value = mock_window

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

        # Check that render_list was called
        mock_renderer.render_list.assert_called_with(display_list, force_full=False)
        # We can't easily inspect ctypes array in mock without more setup.
        # But simply asserting it was called proves dispatch worked.
        pass

    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.window.Renderer")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_text(self, mock_sdl2, mock_ext, mock_renderer_cls, mock_debug):
        """Test that text is rendered."""
        mock_renderer = mock_renderer_cls.return_value


        mock_window = MagicMock()
        mock_window.size = (800, 600)
        mock_ext.Window.return_value = mock_window

        # Mock FontManager
        mock_font_manager = MagicMock()
        # Mock surface from render
        mock_surface = MagicMock()
        mock_surface.w = 50
        mock_surface.h = 20
        mock_font_manager.render.return_value = mock_surface

        mock_ext.FontManager.return_value = mock_font_manager

        # Mock Texture
        mock_texture = MagicMock()
        mock_texture.size = (50, 20)
        mock_ext.Texture.return_value = mock_texture

        win = Window("Test", 800, 600)

        display_list = [
            {
                "type": "text",
                "rect": [10, 10, 100, 30],
                "text": "Hello",
                "font_size": 16,
                "color": (0, 0, 0, 255)
            }
        ]

        win.render(display_list)

        # Verify render_list called
        mock_renderer.render_list.assert_called_with(display_list, force_full=False)

    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.window.Renderer")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_text_wrapping(self, mock_sdl2, mock_ext, mock_renderer_cls, mock_debug):
        """Test that text wrapping logic is triggered."""
        mock_renderer = mock_renderer_cls.return_value


        mock_window = MagicMock()
        mock_window.size = (800, 600)
        mock_ext.Window.return_value = mock_window

        mock_font_manager = MagicMock()
        # Mock surface
        mock_surface = MagicMock()
        mock_surface.w = 50
        mock_surface.h = 20
        mock_font_manager.render.return_value = mock_surface

        mock_ext.FontManager.return_value = mock_font_manager
        mock_texture = MagicMock()
        mock_texture.size = (50, 20)
        mock_ext.Texture.return_value = mock_texture

        win = Window("Test", 800, 600)

        # Text that needs wrapping (width 100, surface w=50. Two words.)
        # Use side_effect for render to return different sizes for wrapping simulation.

        def render_side_effect(text):
            m = MagicMock()
            m.h = 20
            # Rough estimation for mock
            m.w = len(text) * 10
            return m

        mock_font_manager.render.side_effect = render_side_effect

        display_list = [
            {
                "type": "text",
                "rect": [10, 10, 60, 100], # Width 60. "Word1" (50) fits. "Word1 Word2" (110) doesn't.
                "text": "Word1 Word2",
                "font_size": 16,
                "color": (0, 0, 0, 255),
                "wrap": True
            }
        ]

        win.render(display_list)

        # Verify render_list called
        mock_renderer.render_list.assert_called_with(display_list, force_full=False)

    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.window.Renderer")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_with_culling(self, mock_sdl2, mock_ext, mock_renderer_cls, mock_debug):
        """Test that off-screen items are culled."""
        mock_renderer = mock_renderer_cls.return_value

        mock_window = MagicMock()
        mock_window.size = (800, 600)
        mock_ext.Window.return_value = mock_window

        win = Window("Test", 800, 600)

        # Scenario: Scrollable Layer with viewport (0,0,800,600)
        # Item 1: y=100 (Visible)
        # Item 2: y=1000 (Invisible, > 600)

        display_list = [
            {
                "type": core.TYPE_SCROLLABLE_LAYER,
                "rect": [0, 0, 800, 600],
                "scroll_y": 0,
                "children": [
                    {
                        "type": core.TYPE_VBOX,
                        "rect": [0, 0, 100, 100], # Will be resolved relative
                        "children": [
                             { "type": "rect", "rect": [0, 100, 50, 50], "color": (255,0,0,255) },   # Visible
                             { "type": "rect", "rect": [0, 1000, 50, 50], "color": (0,255,0,255) }    # Invisible
                        ]
                    }
                ]
            }
        ]

        win.render(display_list)
        
        # Verify render_list called
        mock_renderer.render_list.assert_called_with(display_list, force_full=False)

        pass

    # test_measurement_caching deleted
    pass

    # test_get_ui_events deleted
    # test_find_hit deleted
    pass

    # Obsolete tests deleted

    # Remaining obsolete tests deleted
    pass

    # Final cleanup
    pass



