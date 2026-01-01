
import unittest
from unittest.mock import MagicMock, patch

from sdl_gui import core
from sdl_gui.window.window import Window


class TestWindowDebugIntegration(unittest.TestCase):

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    @patch("sdl_gui.window.renderer.sdl2.ext") # Patch renderer's sdl2 usage
    @patch("sdl_gui.window.renderer.sdl2")     # Patch renderer's sdl2 usage
    @patch("sdl_gui.window.window.DebugServer") # Mock the DebugServer class
    def test_debug_server_init(self, mock_debug_server_cls, mock_sdl2, mock_ext, mock_rend_sdl2, mock_rend_ext):
        """Test that DebugServer is initialized when debug=True."""
        # Setup mocks to avoid Renderer failure
        mock_window = MagicMock()
        mock_ext.Window.return_value = mock_window
        mock_renderer = MagicMock()
        mock_rend_ext.Renderer.return_value = mock_renderer

        # Init with debug=True
        win = Window("Test", 800, 600, debug=True)

        # Verify DebugServer started
        mock_debug_server_cls.assert_called_once()
        win.debug_server.start.assert_called_once()

        # Init with debug=False
        mock_debug_server_cls.reset_mock()
        win2 = Window("Test", 800, 600, debug=False)
        mock_debug_server_cls.assert_not_called()
        self.assertIsNone(win2.debug_server)

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.renderer.sdl2.ext")
    @patch("sdl_gui.window.renderer.sdl2")
    def test_handle_debug_resize(self, mock_rend_sdl2, mock_rend_ext, mock_debug_cls, mock_sdl2, mock_ext):
        """Test processing of resize command."""
        mock_ext.Window.return_value = MagicMock()
        mock_rend_ext.Renderer.return_value = MagicMock()

        win = Window("Test", 800, 600, debug=True)

        # Call handler directly
        cmd = {"action": "resize", "width": 1024, "height": 768}
        win._handle_debug_command(cmd, [])

        self.assertEqual(win.width, 1024)
        self.assertEqual(win.height, 768)
        # Verify SDL window resize called?
        # win.window.size = (w, h) property setter
        # check if property was set:
        # win.window is a Mock.
        # win.window.size = (1024, 768)
        # We can't easily check property set on MagicMock unless we examine calls or attach PropertyMock.
        # But we updated self.width/height.

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.renderer.sdl2.ext")
    @patch("sdl_gui.window.renderer.sdl2")
    def test_handle_debug_screenshot(self, mock_rend_sdl2, mock_rend_ext, mock_debug_cls, mock_sdl2, mock_ext):
        """Test processing of screenshot command."""
        mock_ext.Window.return_value = MagicMock()
        mock_rend_ext.Renderer.return_value = MagicMock()
        win = Window("Test", 800, 600, debug=True)

        with patch.object(win, 'save_screenshot') as mock_save:
            cmd = {"action": "screenshot", "filename": "test.bmp"}
            win._handle_debug_command(cmd, [])
            mock_save.assert_called_with("test.bmp")

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.renderer.sdl2.ext")
    @patch("sdl_gui.window.renderer.sdl2")
    def test_handle_debug_simulate_click(self, mock_rend_sdl2, mock_rend_ext, mock_debug_cls, mock_sdl2, mock_ext):
        """Test processing of simulate_click command."""
        mock_ext.Window.return_value = MagicMock()
        mock_rend_ext.Renderer.return_value = MagicMock()
        win = Window("Test", 800, 600, debug=True)

        # We need to spy on `_process_mouse_down` or check side effects in ui_events
        # simulating click calls _process_mouse_down(x,y, ui_events)

        ui_events = []
        cmd = {"action": "simulate_click", "x": 100, "y": 100}

        # We can patch _process_mouse_down to verify it's valid
        with patch.object(win, '_process_mouse_down') as mock_proc:
             win._handle_debug_command(cmd, ui_events)
             mock_proc.assert_called_with(100, 100, ui_events)

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    @patch("sdl_gui.window.window.DebugServer")
    @patch("sdl_gui.window.renderer.sdl2.ext")
    @patch("sdl_gui.window.renderer.sdl2")
    def test_get_ui_events_pulls_from_debug(self, mock_rend_sdl2, mock_rend_ext, mock_debug_cls, mock_sdl2, mock_ext):
        """Test that get_ui_events pulls actions from the debug server."""
        mock_ext.Window.return_value = MagicMock()
        mock_rend_ext.Renderer.return_value = MagicMock()

        # Mock SDL events to return empty list
        mock_ext.get_events.return_value = []

        win = Window("Test", 800, 600, debug=True)

        # Setup Debug Server mock to return an event
        mock_server_instance = win.debug_server
        mock_server_instance.get_pending_actions.return_value = [
            ("event", {"type": "custom_event"}),
            ("command", {"action": "resize", "width": 500, "height": 500})
        ]

        events = win.get_ui_events()

        # Verify custom event made it
        custom = next((e for e in events if e.get("type") == "custom_event"), None)
        self.assertIsNotNone(custom)

        # Verify command side effects (resize)
        self.assertEqual(win.width, 500)

        # Verify quit command translation
        mock_server_instance.get_pending_actions.return_value = [
            ("command", {"action": "quit"})
        ]
        events_quit = win.get_ui_events()
        quit_evt = next((e for e in events_quit if e.get("type") == core.EVENT_QUIT), None)
        self.assertIsNotNone(quit_evt)

if __name__ == '__main__':
    unittest.main()
