
import json
import socket
import unittest
from unittest.mock import MagicMock, patch

from sdl_gui import core
from sdl_gui.debug.server import DebugServer
from sdl_gui.window.renderer import Renderer
from sdl_gui.window.window import Window

class TestDebugDump(unittest.TestCase):

    @patch("sdl_gui.window.renderer.sdl2.ext")
    @patch("sdl_gui.rendering.text_renderer.sdlttf")
    def test_renderer_sanitization(self, mock_ttf, mock_rend_ext):
        """Test that Renderer correctly sanitizes display list for JSON serialization."""
        mock_window = MagicMock()
        renderer = Renderer(mock_window)
        
        def my_callback(): pass
        
        display_list = [
            {
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_COLOR: (255, 0, 0, 255),
                "extra": "info"
            },
            {
                core.KEY_TYPE: core.TYPE_IMAGE,
                core.KEY_SOURCE: b"fake_image_bytes",
                "callback": my_callback,
                core.KEY_CHILDREN: [
                    {core.KEY_TYPE: core.TYPE_TEXT, core.KEY_TEXT: "nested"}
                ]
            }
        ]
        
        sanitized = renderer._sanitize_list(display_list)
        
        # Check first item
        self.assertEqual(sanitized[0][core.KEY_COLOR], [255, 0, 0, 255])
        self.assertEqual(sanitized[0]["extra"], "info")
        
        # Check second item (sanitization of non-serializable)
        self.assertTrue(sanitized[1][core.KEY_SOURCE].startswith("<bytes:"))
        self.assertTrue(sanitized[1]["callback"].startswith("<callable:"))
        self.assertEqual(sanitized[1][core.KEY_CHILDREN][0][core.KEY_TEXT], "nested")
        
        # Verify it's actually JSON serializable
        json_str = json.dumps(sanitized)
        self.assertIsInstance(json_str, str)

    def test_debug_server_dump_command(self):
        """Test that DebugServer handles dump_display_list correctly."""
        server = DebugServer(port=9999)
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        
        test_data = [{"id": "test_element"}]
        server.display_list_provider = MagicMock(return_value=test_data)
        
        # Simulate dump command
        cmd_data = json.dumps({"type": "dump_display_list"}).encode('utf-8') + b'\n'
        mock_conn.recv.side_effect = [cmd_data, b'']
        
        server.running = True
        server._handle_client(mock_conn)
        
        # Verify provider was called
        server.display_list_provider.assert_called_once()
        
        # Verify response contains the data
        # We need to capture what was sent to sendall
        sent_data = b"".join([call.args[0] for call in mock_conn.sendall.call_args_list])
        resp = json.loads(sent_data.decode('utf-8').strip())
        
        self.assertEqual(resp["status"], "ok")
        self.assertEqual(resp["data"], test_data)

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    @patch("sdl_gui.window.renderer.sdl2.ext")
    @patch("sdl_gui.window.renderer.sdl2")
    @patch("sdl_gui.window.window.DebugServer")
    def test_window_dump_integration(self, mock_debug_server_cls, *args):
        """Test that Window correctly links Renderer to DebugServer."""
        mock_server = MagicMock()
        mock_debug_server_cls.return_value = mock_server
        
        win = Window("Test", 800, 600, debug=True)
        
        # Verify that debug_server has the provider set to renderer's method
        self.assertEqual(mock_server.display_list_provider, win.renderer.get_last_display_list)

if __name__ == '__main__':
    unittest.main()
