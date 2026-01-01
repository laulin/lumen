import unittest
from unittest.mock import MagicMock, patch

from sdl_gui import core
from sdl_gui.window.window import Window


class TestWindowRichText(unittest.TestCase):
    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.renderer.sdlttf.TTF_Init")
    @patch("sdl_gui.window.window.sdl2")
    @patch("sdl_gui.window.renderer.sdl2")
    def test_render_rich_text_link_markdown(self, mock_rend_sdl2, mock_win_sdl2, mock_ttf, mock_debug):
        mock_renderer_cls = mock_rend_sdl2.ext.Renderer
        mock_renderer = mock_renderer_cls.return_value
        
        # Mock FontManager
        mock_fm = MagicMock()
        mock_fm.render.return_value = MagicMock(w=10, h=10)
        # FontManager is in sdl_gui.window.renderer usually or imported?
        # It's referenced via sdl2.ext.FontManager usually.
        mock_rend_sdl2.ext.FontManager.return_value = mock_fm

        mock_window = MagicMock()
        mock_window.size = (100, 100)
        mock_win_sdl2.ext.Window.return_value = mock_window

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
        
        # This test relies on internal logic of Renderer to parse text and add hits.
        # But we mocked the `Renderer` class dependency (via sdl2.ext.Renderer)? 
        # No, we mocked the *libraries* `sdl2` and `sdl2.ext`.
        # `d = Renderer(...)` calls `self.renderer = sdl2.ext.Renderer(...)`.
        # `d.render_list()` executes real python code in `Renderer` class.
        # `d._render_text` executes real code.
        # `d.font_manager` -> `sdl2.ext.FontManager`.
        # `d._calculate_rich_text_lines` -> calls font manager.
        # `d.hit_list` is a real list in `Renderer`.
        
        # So we can check `win.renderer.hit_list`.
        
        hits = win.renderer.get_hit_list()
        found_link = False
        for rect, data in hits:
             if data.get("type") == "link" and data.get("target") == "mylink":
                 found_link = True
                 break
        self.assertTrue(found_link, "Link item not found in hit list")
