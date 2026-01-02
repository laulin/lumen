
import json
import socket
import threading
import time
import unittest
from unittest.mock import MagicMock

from sdl_gui.debug.server import DebugServer
from tools.debug_client import DebugClient

class TestE2EDump(unittest.TestCase):

    def test_e2e_dump(self):
        """Test the full chain: DebugClient -> Socket -> DebugServer -> Provider."""
        port = 10001
        server = DebugServer(port=port)
        
        test_data = [
            {"type": "rect", "color": [255, 0, 0, 255]},
            {"type": "text", "text": "Hello E2E"}
        ]
        
        server.display_list_provider = MagicMock(return_value=test_data)
        server.start()
        
        # Give server a moment to start
        time.sleep(0.5)
        
        try:
            client = DebugClient(port=port)
            client.connect()
            
            # We want to capture the client's output or just check the response
            # Since client._send prints, we'll patch print or just call the methods
            
            # Let's verify the response directly from the socket if we want to be sure,
            # or just use the client's send_command logic.
            
            # We'll use a local helper to capture what client receives
            client.sock.sendall((json.dumps({"type": "dump_display_list"}) + "\n").encode('utf-8'))
            
            # Wait for response
            resp_str = ""
            client.sock.settimeout(2.0)
            while True:
                chunk = client.sock.recv(4096).decode('utf-8')
                resp_str += chunk
                if "\n" in resp_str:
                    break
            
            resp = json.loads(resp_str.strip())
            
            self.assertEqual(resp["status"], "ok")
            self.assertEqual(resp["data"], test_data)
            server.display_list_provider.assert_called_once()
            
        finally:
            server.stop()
            if client.sock:
                client.sock.close()

if __name__ == '__main__':
    unittest.main()
