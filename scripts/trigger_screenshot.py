import socket
import json
import time

def trigger():
    retries = 5
    while retries > 0:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', 9999))
            
            # Send Screenshot Command
            cmd = {
                "type": "command",
                "action": "screenshot",
                "filename": "flexbox_verification.bmp"
            }
            s.sendall(json.dumps(cmd).encode('utf-8') + b'\n')
            
            # Read response
            resp = s.recv(4096)
            print("Response:", resp.decode('utf-8'))
            
            # Send Quit Command to clean up
            cmd_quit = {"type": "command", "action": "quit"}
            s.sendall(json.dumps(cmd).encode('utf-8') + b'\n')
            s.close()
            return
        except Exception as e:
            print(f"Connection failed: {e}. Retrying...")
            time.sleep(1)
            retries -= 1

if __name__ == "__main__":
    trigger()
