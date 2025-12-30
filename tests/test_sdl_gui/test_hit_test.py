import unittest
from unittest.mock import MagicMock, patch
from sdl_gui.window.window import Window
from sdl_gui import core

class TestWindowHitTest(unittest.TestCase):
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_passive_layer_passthrough(self, mock_sdl2, mock_ext):
        """
        Test that a top-level passive layer (no events) does NOT block 
        clicks to an underlying active element.
        """
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        mock_win_instance = MagicMock()
        mock_win_instance.size = (800, 600)
        mock_ext.Window.return_value = mock_win_instance
        
        win = Window("Test", 800, 600)
        
        # 1. Structure:
        # - Rect (Listener) at 0,0 100x100
        # - Layer (Passive) at 0,0 800x600 (Covers Rect)
        
        display_list = [
            {
                "type": "rect",
                "rect": [0, 0, 100, 100],
                "id": "bottom_rect",
                "listen_events": [core.EVENT_CLICK]
            },
            {
                "type": "layer",
                "rect": [0, 0, 800, 600],
                "id": "top_layer", # No listen_events
                "children": []
            }
        ]
        
        win.render(display_list)
        
        # 2. Click at 50,50 (Hits both Layer and Rect)
        mock_event = MagicMock()
        mock_event.type = mock_sdl2.SDL_MOUSEBUTTONDOWN
        mock_event.button.x = 50
        mock_event.button.y = 50
        mock_ext.get_events.return_value = [mock_event]
        
        # 3. Get Events
        ui_events = win.get_ui_events()
        
        # 4. Expectation: The click should find 'bottom_rect' because 'top_layer' 
        # doesn't listen to clicks.
        self.assertEqual(len(ui_events), 1)
        self.assertEqual(ui_events[0]["target"], "bottom_rect")
