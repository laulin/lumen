
import json
import socket
import unittest
from unittest.mock import MagicMock

from sdl_gui.debug.server import DebugServer


class TestDebugServer(unittest.TestCase):

    def setUp(self):
        self.mock_socket = MagicMock()
        self.mock_socket_factory = MagicMock(return_value=self.mock_socket)
        # Default accept behavior: timeout so the serving loop just spins quietly
        self.mock_socket.accept.side_effect = socket.timeout
        self.server = DebugServer(port=9999, socket_factory=self.mock_socket_factory)

    def tearDown(self):
        self.server.stop()

    def test_init(self):
        """Test server initialization."""
        self.assertEqual(self.server.port, 9999)
        self.assertFalse(self.server.running)
        self.assertTrue(self.server.command_queue.empty())

    def test_start(self):
        """Test starting the server binds to port."""
        self.server.start()
        self.assertTrue(self.server.running)
        self.mock_socket_factory.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)
        self.mock_socket.bind.assert_called_with(('127.0.0.1', 9999))
        self.mock_socket.listen.assert_called_with(1)

    def test_double_start(self):
        """Test starting twice does nothing."""
        self.server.start()
        self.server.start()
        self.mock_socket_factory.assert_called_once()

    def test_handle_client_command(self):
        """Test handling a valid command from a client."""
        # Setup mock connection
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn

        # Simulate incoming data: valid command then close
        cmd_data = json.dumps({"type": "command", "action": "test_cmd"}).encode('utf-8') + b'\n'
        mock_conn.recv.side_effect = [cmd_data, b'']

        self.server.running = True
        self.server._handle_client(mock_conn)

        # Verify queue
        self.assertFalse(self.server.command_queue.empty())
        cmd_type, data = self.server.command_queue.get()
        self.assertEqual(cmd_type, "command")
        self.assertEqual(data["action"], "test_cmd")

        # Check response
        expected_resp = json.dumps({"status": "ok"}).encode('utf-8') + b'\n'
        mock_conn.sendall.assert_called_with(expected_resp)

    def test_handle_client_event(self):
        """Test handling a valid event from a client."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn

        event_payload = {"type": "event", "event": {"type": "click", "x": 10}}
        data = json.dumps(event_payload).encode('utf-8') + b'\n'
        mock_conn.recv.side_effect = [data, b'']

        self.server.running = True
        self.server._handle_client(mock_conn)

        cmd_type, data = self.server.command_queue.get()
        self.assertEqual(cmd_type, "event")
        self.assertEqual(data["type"], "click")

    def test_handle_invalid_json(self):
        """Test handling invalid JSON."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn

        mock_conn.recv.side_effect = [b"invalid json\n", b'']

        self.server.running = True
        self.server._handle_client(mock_conn)

        self.assertTrue(self.server.command_queue.empty())

        # Check error response
        expected_resp = json.dumps({"status": "error", "message": "Invalid JSON"}).encode('utf-8') + b'\n'
        # Note: the exact error message might vary depending on impl, checking generic "error" status is safer or exact match if known.
        # My impl says: self._send_response(conn, "error", "Invalid JSON")
        mock_conn.sendall.assert_called_with(expected_resp)

    def test_get_pending_actions(self):
        """Test retrieving pending actions."""
        self.server.command_queue.put(("command", {"a": 1}))
        self.server.command_queue.put(("event", {"b": 2}))

        actions = self.server.get_pending_actions()
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0][0], "command")
        self.assertEqual(actions[1][0], "event")
        self.assertTrue(self.server.command_queue.empty())

if __name__ == '__main__':
    unittest.main()
