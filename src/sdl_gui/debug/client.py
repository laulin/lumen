import socket
import json
import time
from typing import Any, Dict, Optional, Union

class DebugClient:
    """
    Client for the DebugServer to allow automated testing and control.
    """
    def __init__(self, host: str = '127.0.0.1', port: int = 9999):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None

    def connect(self) -> None:
        """Connect to the DebugServer."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except Exception as e:
            self.sock.close()
            self.sock = None
            # Raise exception so the caller knows connection failed
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}") from e

    def close(self) -> None:
        """Close the connection."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def send_command(self, action: str, **kwargs: Any) -> Dict[str, Any]:
        """Send a general command to the server."""
        cmd = {"type": "command", "action": action}
        cmd.update(kwargs)
        return self._send_and_receive(cmd)

    def send_event(self, event_type: str, **kwargs: Any) -> Dict[str, Any]:
        """Send an event to the server."""
        evt = {"type": event_type}
        evt.update(kwargs)
        payload = {"type": "event", "event": evt}
        return self._send_and_receive(payload)

    def dump_display_list(self) -> Dict[str, Any]:
        """Request a dump of the current display list."""
        payload = {"type": "dump_display_list"}
        return self._send_and_receive(payload)

    def resize(self, width: int, height: int) -> Dict[str, Any]:
        """Resize the window."""
        return self.send_command("resize", width=width, height=height)

    def screenshot(self, filename: str) -> Dict[str, Any]:
        """Take a screenshot."""
        return self.send_command("screenshot", filename=filename)

    def mouse_move(self, x: int, y: int) -> Dict[str, Any]:
        """Simulate mouse move."""
        return self.send_command("mouse_move", x=x, y=y)

    def mouse_down(self, x: int, y: int) -> Dict[str, Any]:
        """Simulate mouse down."""
        return self.send_command("mouse_down", x=x, y=y)

    def mouse_up(self, x: int, y: int) -> Dict[str, Any]:
        """Simulate mouse up."""
        return self.send_command("mouse_up", x=x, y=y)

    def click_at(self, x: int, y: int) -> Dict[str, Any]:
        """Simulate a click (mouse down + mouse up logic handled by server if implemented, or just a helper).
        The server supports 'simulate_click' action which usually does a down/up sequence or triggers a click event.
        """
        return self.send_command("simulate_click", x=x, y=y)

    def quit(self) -> Dict[str, Any]:
        """Send quit command."""
        return self.send_command("quit")

    def _send_and_receive(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to send JSON and receive JSON response."""
        if not self.sock:
            raise ConnectionError("Not connected")

        try:
            data = json.dumps(payload) + "\n"
            self.sock.sendall(data.encode('utf-8'))
            
            resp_str = self._recv_response()
            if not resp_str:
                raise ConnectionError("Connection closed or empty response")
            
            return json.loads(resp_str)
        except Exception as e:
            raise ConnectionError(f"Error during communication: {e}") from e

    def _recv_response(self) -> str:
        """Receive a single line response."""
        if not self.sock:
            return ""
        
        data = b""
        while True:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
        return data.decode('utf-8').strip()
