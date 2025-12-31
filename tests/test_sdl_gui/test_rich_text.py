import unittest
from unittest.mock import MagicMock, patch
from sdl_gui import core
from sdl_gui.window.window import Window

class TestWindowRichText(unittest.TestCase):
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_rich_text_link_markdown(self, mock_sdl2, mock_ext):
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        mock_window = MagicMock()
        mock_window.size = (100, 100)
        mock_ext.Window.return_value = mock_window
        
        mock_fm = MagicMock()
        mock_fm.render.return_value = MagicMock(w=10, h=10)
        mock_ext.FontManager.return_value = mock_fm
        
        # Mock Texture to have a size property (width, height)
        mock_texture = MagicMock()
        mock_texture.size = (10, 10)
        mock_ext.Texture.return_value = mock_texture
        
        win = Window("Test", 100, 100)
        win.ttf_available = True
        
        # Use markdown syntax
        item = {
            core.KEY_TYPE: core.TYPE_TEXT,
            core.KEY_RECT: [0, 0, 100, 100],
            core.KEY_TEXT: "[Link](mylink)",
            core.KEY_MARKUP: True
        }
        
        win.render([item])
        
        # Verify hit list has the link
        hits = win._hit_list
        found_link = False
        for rect, data in hits:
            if data.get("type") == "link" and data.get("target") == "mylink":
                found_link = True
                break
        self.assertTrue(found_link, "Link item not found in hit list")
