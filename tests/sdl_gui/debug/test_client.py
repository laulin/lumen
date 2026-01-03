import unittest
import threading
import time
import socket
from queue import Queue
from typing import Any, Tuple

from sdl_gui.debug.server import DebugServer
from sdl_gui.debug.client import DebugClient

class TestDebugClientIntegration(unittest.TestCase):
    def setUp(self):
        # Find a free port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        self.port = sock.getsockname()[1]
        sock.close()

        # Start DebugServer
        self.server = DebugServer(port=self.port)
        self.server.start()
        
        # Wait a bit for server to start
        time.sleep(0.1)

        self.client = DebugClient(port=self.port)

    def tearDown(self):
        self.client.close()
        self.server.stop()
        if self.server.thread:
            self.server.thread.join(timeout=1.0)

    def test_connect_and_send_command(self):
        self.client.connect()
        resp = self.client.send_command("test_cmd", foo="bar")
        self.assertEqual(resp.get("status"), "ok")

        # Verify server received it
        # We need to poll the server's queue
        # Since server.get_pending_actions clears the queue, we can check it.
        # But we need to make sure the server has processed the socket data.
        # send_command waits for response, so server MUST have processed it.
        
        actions = self.server.get_pending_actions()
        self.assertEqual(len(actions), 1)
        action_type, payload = actions[0]
        self.assertEqual(action_type, "command")
        self.assertEqual(payload["action"], "test_cmd")
        self.assertEqual(payload["foo"], "bar")

    def test_send_event(self):
        self.client.connect()
        resp = self.client.send_event("click", x=10, y=20)
        self.assertEqual(resp.get("status"), "ok")

        actions = self.server.get_pending_actions()
        self.assertEqual(len(actions), 1)
        action_type, payload = actions[0]
        self.assertEqual(action_type, "event")
        self.assertEqual(payload["type"], "click")
        self.assertEqual(payload["x"], 10)
        self.assertEqual(payload["y"], 20)

    def test_dump_display_list(self):
        # Mock display list provider on server
        mock_data = [{"type": "rect", "x": 0, "y": 0}]
        self.server.display_list_provider = lambda: mock_data

        self.client.connect()
        resp = self.client.dump_display_list()
        
        self.assertEqual(resp.get("status"), "ok")
        self.assertEqual(resp.get("data"), mock_data)

    def test_resize_helper(self):
        self.client.connect()
        self.client.resize(800, 600)
        
        actions = self.server.get_pending_actions()
        self.assertEqual(len(actions), 1)
        _, payload = actions[0]
        self.assertEqual(payload["action"], "resize")
        self.assertEqual(payload["width"], 800)
        self.assertEqual(payload["height"], 600)

    def test_connection_error_handling(self):
        # Test connecting to wrong port
        bad_client = DebugClient(port=self.port + 1)
        with self.assertRaises(ConnectionError):
            bad_client.connect()
        
        # Test sending without connection
        bad_client2 = DebugClient(port=self.port)
        with self.assertRaises(ConnectionError):
            bad_client2.send_command("foo")

if __name__ == '__main__':
    unittest.main()
