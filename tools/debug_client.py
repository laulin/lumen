import json
import argparse
import sys
import os

# Add src to path so we can import sdl_gui
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sdl_gui.debug.client import DebugClient

def print_response(resp):
    if "data" in resp:
        print(f"Status: {resp.get('status')}")
        print("Data:")
        print(json.dumps(resp["data"], indent=2))
    else:
        print(f"Response: {resp}")

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
    
    try:
        client.connect()
        print(f"Connected to {args.host}:{args.port}")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    try:
        resp = {}
        if args.command == "resize":
            resp = client.resize(width=args.width, height=args.height)
        elif args.command == "screenshot":
            resp = client.screenshot(filename=args.filename)
        elif args.command == "mouse_move":
            resp = client.mouse_move(x=args.x, y=args.y)
        elif args.command == "mouse_down":
            resp = client.mouse_down(x=args.x, y=args.y)
        elif args.command == "mouse_up":
            resp = client.mouse_up(x=args.x, y=args.y)
        elif args.command == "click_at":
             resp = client.click_at(x=args.x, y=args.y)
        elif args.command == "event":
            data = {}
            if args.data:
                data = json.loads(args.data)
            if args.target:
                data["target"] = args.target
            resp = client.send_event(args.type, **data)
        elif args.command == "quit":
            resp = client.quit()
        elif args.command == "dump":
            resp = client.dump_display_list()
        
        if resp:
            print_response(resp)
            
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        client.close()
