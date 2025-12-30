import unittest
from unittest.mock import MagicMock, patch
from sdl_gui.window.window import Window
from sdl_gui import core

class TestWindowCoverage(unittest.TestCase):
    def setUp(self):
        # Patch sdl2 init
        self.patcher1 = patch("sdl_gui.window.window.sdl2.ext.init")
        self.patcher2 = patch("sdl_gui.window.window.sdl2.sdlttf.TTF_Init")
        self.patcher3 = patch("sdl_gui.window.window.sdl2.ext.Window")
        self.patcher4 = patch("sdl_gui.window.window.sdl2.ext.Renderer")
        
        self.mock_init = self.patcher1.start()
        self.mock_ttf = self.patcher2.start()
        self.mock_win_cls = self.patcher3.start()
        self.mock_rend_cls = self.patcher4.start()
        
        self.mock_window = MagicMock()
        self.mock_window.size = (100, 100)
        self.mock_win_cls.return_value = self.mock_window
        
        self.mock_renderer = MagicMock()
        self.mock_rend_cls.return_value = self.mock_renderer
        
    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()

    def test_resolve_val_invalid(self):
        """Test _resolve_val with invalid strings."""
        win = Window("Test", 100, 100)
        # Valid percentage
        self.assertEqual(win._resolve_val("50%", 200), 100)
        # Invalid percentage
        self.assertEqual(win._resolve_val("bad%", 200), 0)
        # Not a percentage string
        self.assertEqual(win._resolve_val("bad", 200), 0)
        
    def test_show_window(self):
        """Test show method."""
        win = Window("Test", 100, 100)
        win.show()
        self.mock_window.show.assert_called_once()
        
    def test_render_no_ttf(self):
        """Test rendering text when TTF is not available."""
        win = Window("Test", 100, 100)
        win.ttf_available = False
        
        item = {
            core.KEY_TYPE: core.TYPE_TEXT,
            core.KEY_TEXT: "Hello"
        }
        # Should return early and do nothing (no crash)
        win._render_text(item, (0,0,100,100))
        
    def test_render_empty_text(self):
        """Test rendering empty text."""
        win = Window("Test", 100, 100)
        win.ttf_available = True
        
        item = {
            core.KEY_TYPE: core.TYPE_TEXT,
            core.KEY_TEXT: ""
        }
        win._render_text(item, (0,0,100,100))
        # No font manager access
        self.assertFalse(win._font_cache)

    def test_render_hbox_coverage(self):
        """Test rendering HBox to cover padding/margin loops."""
        win = Window("Test", 100, 100)
        
        child = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 10, 10],
            core.KEY_MARGIN: (1, 1, 1, 1)
        }
        hbox = {
            core.KEY_TYPE: core.TYPE_HBOX,
            core.KEY_RECT: [0, 0, 100, 100],
            core.KEY_PADDING: (5, 5, 5, 5),
            core.KEY_CHILDREN: [child]
        }
        
        # We need to call _render_item to trigger _render_hbox
        win._render_item(hbox, (0,0,100,100))
        
        # Verify renderer fill called for child rect
        self.mock_renderer.fill.assert_called()

