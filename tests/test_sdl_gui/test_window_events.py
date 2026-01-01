import unittest
from unittest.mock import MagicMock, patch

from sdl_gui import core
from sdl_gui.window.window import Window


class TestWindowEvents(unittest.TestCase):
    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.window.Renderer")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_click_event(self, mock_sdl2, mock_ext, mock_renderer_cls, mock_debug):
        """Test that click events are correctly returned."""
        # Mock renderer & window
        mock_renderer = mock_renderer_cls.return_value
        mock_win_instance = MagicMock()
        mock_win_instance.size = (800, 600)
        mock_ext.Window.return_value = mock_win_instance

        win = Window("Test", 800, 600)

        # Mock SDL get_events
        mock_event = MagicMock()
        mock_event.type = mock_sdl2.SDL_MOUSEBUTTONDOWN
        mock_event.button.x = 50
        mock_event.button.y = 50
        mock_ext.get_events.return_value = [mock_event]

        # 1. Render a scene with a clickable rect
        display_list = [
            {
                "type": "rect",
                "rect": [0, 0, 100, 100],
                "color": (255, 0, 0, 255),
                "id": "my_btn",
                "listen_events": [core.EVENT_CLICK]
            }
        ]
        win.render(display_list)
        
        # Mock what logic populates? No, render logic populates hit_list in real Renderer.
        # Since we mock Renderer, we must manually populate hit_list return value
        item = display_list[0]
        rect = (0, 0, 100, 100)
        mock_renderer.get_hit_list.return_value = [(rect, item)]

        # 2. Get UI Events
        ui_events = win.get_ui_events()

        # 3. Verify
        self.assertEqual(len(ui_events), 2)
        # ui_events[0] is TICK, [1] is CLICK usually (depends on append order)
        # Check that one of them is CLICK
        event_types = [e["type"] for e in ui_events]
        self.assertIn(core.EVENT_CLICK, event_types)
        
        click_event = next(e for e in ui_events if e["type"] == core.EVENT_CLICK)
        self.assertEqual(click_event["target"], "my_btn")


    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.window.Renderer")
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_click_miss(self, mock_sdl2, mock_ext, mock_renderer_cls, mock_debug):
        """Test that clicks outside the rect do not trigger event."""
        mock_renderer = mock_renderer_cls.return_value
        mock_win_instance = MagicMock()
        mock_win_instance.size = (800, 600)
        mock_ext.Window.return_value = mock_win_instance

        win = Window("Test", 800, 600)

        # Mock SDL get_events (Click at 200, 200)
        mock_event = MagicMock()
        mock_event.type = mock_sdl2.SDL_MOUSEBUTTONDOWN
        mock_event.button.x = 200
        mock_event.button.y = 200
        mock_ext.get_events.return_value = [mock_event]

        # Rect at (0,0) size 100x100
        display_list = [
            {
                "type": "rect",
                "rect": [0, 0, 100, 100],
                "id": "my_btn",
                "listen_events": [core.EVENT_CLICK]
            }
        ]
        win.render(display_list)

        ui_events = win.get_ui_events()

        # Should have 1 event (TICK)
        self.assertEqual(len(ui_events), 1)
        self.assertEqual(ui_events[0]["type"], core.EVENT_TICK)

