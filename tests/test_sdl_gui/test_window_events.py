import unittest
from unittest.mock import MagicMock, patch
from sdl_gui.window.window import Window
from sdl_gui import core

class TestWindowEvents(unittest.TestCase):
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_click_event(self, mock_sdl2, mock_ext):
        """Test that click events are correctly dispatched."""
        # Mock renderer & window
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        mock_win_instance = MagicMock()
        mock_win_instance.size = (800, 600)
        mock_ext.Window.return_value = mock_win_instance
        
        win = Window("Test", 800, 600)
        
        # Define callback
        callback_called = False
        def on_click():
            nonlocal callback_called
            callback_called = True
            
        # 1. Render a scene with a clickable rect at (0,0) size 100x100
        display_list = [
            {
                "type": "rect",
                "rect": [0, 0, 100, 100],
                "color": (255, 0, 0, 255),
                "events": {
                    core.EVENT_CLICK: on_click
                }
            }
        ]
        win.render(display_list)
        
        # 2. Simulate Click Event at (50, 50)
        mock_event = MagicMock()
        mock_event.type = mock_sdl2.SDL_MOUSEBUTTONDOWN
        mock_event.button.x = 50
        mock_event.button.y = 50
        
        # 3. Dispatch events
        win.dispatch_events([mock_event])
        
        self.assertTrue(callback_called, "Click callback should have been called")

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_click_miss(self, mock_sdl2, mock_ext):
        """Test that clicks outside the rect do not trigger callback."""
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        mock_win_instance = MagicMock()
        mock_win_instance.size = (800, 600)
        mock_ext.Window.return_value = mock_win_instance
        
        win = Window("Test", 800, 600)
        
        callback_called = False
        def on_click():
            nonlocal callback_called
            callback_called = True
            
        # Rect at (0,0) size 100x100
        display_list = [
            {
                "type": "rect",
                "rect": [0, 0, 100, 100],
                "events": { core.EVENT_CLICK: on_click }
            }
        ]
        win.render(display_list)
        
        # Click at (200, 200)
        mock_event = MagicMock()
        mock_event.type = mock_sdl2.SDL_MOUSEBUTTONDOWN
        mock_event.button.x = 200
        mock_event.button.y = 200
        
        win.dispatch_events([mock_event])
        
        self.assertFalse(callback_called, "Callback should NOT be called for miss")
