
import socket
import json
import argparse
import sys

class DebugClient:
    def __init__(self, host='127.0.0.1', port=9999):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect: {e}")
            sys.exit(1)

    def send_command(self, action, **kwargs):
        cmd = {"type": "command", "action": action}
        cmd.update(kwargs)
        self._send(cmd)

    def send_event(self, event_type, **kwargs):
        evt = {"type": event_type}
        evt.update(kwargs)
        payload = {"type": "event", "event": evt}
        self._send(payload)

    def dump_display_list(self):
        payload = {"type": "dump_display_list"}
        self._send(payload)

    def _send(self, payload):
        try:
            data = json.dumps(payload) + "\n"
            self.sock.sendall(data.encode('utf-8'))
            resp_str = self._recv_response()
            if resp_str:
                resp = json.loads(resp_str)
                if "data" in resp:
                    print(f"Status: {resp.get('status')}")
                    print("Data:")
                    print(json.dumps(resp["data"], indent=2))
                else:
                    print(f"Response: {resp}")
            else:
                print("No response received")
        except Exception as e:
            print(f"Error sending/receiving: {e}")

    def _recv_response(self):
        # simple line reader
        if not self.sock: return
        data = b""
        while True:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
        return data.decode('utf-8').strip()

    def close(self):
        if self.sock: self.sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lumen GUI Debug Client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9999)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Resize
    p_resize = subparsers.add_parser("resize")
    p_resize.add_argument("width", type=int)
    p_resize.add_argument("height", type=int)

    # Screenshot
    p_shot = subparsers.add_parser("screenshot")
    p_shot.add_argument("filename", default="debug_screenshot.bmp")

    # Mouse
    p_move = subparsers.add_parser("mouse_move")
    p_move.add_argument("x", type=int); p_move.add_argument("y", type=int)
    
    p_mdown = subparsers.add_parser("mouse_down")
    p_mdown.add_argument("x", type=int); p_mdown.add_argument("y", type=int)

    p_mup = subparsers.add_parser("mouse_up")
    p_mup.add_argument("x", type=int); p_mup.add_argument("y", type=int)
    
    # Simulate Click (Down+Up)
    p_click = subparsers.add_parser("click_at")
    p_click.add_argument("x", type=int); p_click.add_argument("y", type=int)

    # Event
    p_event = subparsers.add_parser("event")
    p_event.add_argument("type", help="Event type (e.g. click)")
    p_event.add_argument("--target", help="Target ID")
    p_event.add_argument("--data", help="Additional JSON data")

    # Quit
    p_quit = subparsers.add_parser("quit")

    # Dump
    p_dump = subparsers.add_parser("dump")

    args = parser.parse_args()
    client = DebugClient(args.host, args.port)
    client.connect()

    try:
        if args.command == "resize":
            client.send_command("resize", width=args.width, height=args.height)
        elif args.command == "screenshot":
            client.send_command("screenshot", filename=args.filename)
        elif args.command == "mouse_move":
            client.send_command("mouse_move", x=args.x, y=args.y)
        elif args.command == "mouse_down":
            client.send_command("mouse_down", x=args.x, y=args.y)
        elif args.command == "mouse_up":
            client.send_command("mouse_up", x=args.x, y=args.y)
        elif args.command == "click_at":
             client.send_command("simulate_click", x=args.x, y=args.y)
        elif args.command == "event":
            data = {}
            if args.data:
                data = json.loads(args.data)
            if args.target:
                data["target"] = args.target
            # Merge
            client.send_event(args.type, **data)
        elif args.command == "quit":
            client.send_command("quit")
        elif args.command == "dump":
            client.dump_display_list()
    finally:
        client.close()
