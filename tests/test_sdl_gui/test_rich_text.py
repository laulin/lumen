import unittest
from unittest.mock import MagicMock, patch
from sdl_gui import text_utils, core
from sdl_gui.window.window import Window

class TestTextUtils(unittest.TestCase):
    def test_parse_simple(self):
        text = "Hello World"
        segments = text_utils.parse_rich_text(text)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "Hello World")
        self.assertFalse(segments[0].bold)
        
    def test_parse_bold(self):
        text = "Hello <b>World</b>"
        segments = text_utils.parse_rich_text(text)
        # "Hello ", "World"
        # depends on splitting behavior.
        # regex split: "Hello ", "<b>", "World", "</b>"
        # "Hello " is segment 1
        # "World" is segment 2 (bold)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].text, "Hello ")
        self.assertFalse(segments[0].bold)
        self.assertEqual(segments[1].text, "World")
        self.assertTrue(segments[1].bold)
        
    def test_parse_color(self):
        text = "<color=#FF0000>Red</color>"
        segments = text_utils.parse_rich_text(text)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].color, (255, 0, 0, 255))
        
    def test_parse_link(self):
        text = "<link=target>Click</link>"
        segments = text_utils.parse_rich_text(text)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].link_target, "target")
        
    def test_nested(self):
        text = "<b><color=#00FF00>Green Bold</color></b>"
        segments = text_utils.parse_rich_text(text)
        self.assertEqual(len(segments), 1)
        self.assertTrue(segments[0].bold)
        self.assertEqual(segments[0].color, (0, 255, 0, 255))

class TestWindowRichText(unittest.TestCase):
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_render_rich_text_link(self, mock_sdl2, mock_ext):
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        mock_window = MagicMock()
        mock_window.size = (100, 100)
        mock_ext.Window.return_value = mock_window
        
        mock_fm = MagicMock()
        mock_fm.render.return_value = MagicMock(w=10, h=10)
        mock_ext.FontManager.return_value = mock_fm
        
        win = Window("Test", 100, 100)
        win.ttf_available = True
        
        item = {
            core.KEY_TYPE: core.TYPE_TEXT,
            core.KEY_RECT: [0, 0, 100, 100],
            core.KEY_TEXT: "<link=mylink>Link</link>",
            core.KEY_MARKUP: True
        }
        
        win.render([item])
        
        # Verify hit list has the link
        # hit_list item: (rect, data)
        # We expect one hit item for the link
        hits = win._hit_list
        found_link = False
        for rect, data in hits:
            if data.get("type") == "link" and data.get("target") == "mylink":
                found_link = True
                break
        self.assertTrue(found_link, "Link item not found in hit list")
