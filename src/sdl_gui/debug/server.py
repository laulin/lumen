
import json
import logging
import socket
import threading
from queue import Queue
from typing import Any, List, Optional, Tuple


class DebugServer:
    """
    A TCP server running in a background thread that listens for debug commands
    and events from a remote client.
    """
    def __init__(self, port: int = 9999, socket_factory=None):
        self.port = port
        self.host = '127.0.0.1'
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.socket_factory = socket_factory or socket.socket

        # Thread-safe queue for commands/events to be consumed by main thread
        # Format: (type_str, data_dict)
        self.command_queue: Queue[Tuple[str, Any]] = Queue()

    def start(self) -> None:
        """Start the debug server in a separate thread."""
        if self.running:
            return

        self.running = True
        self.server_socket = self.socket_factory(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            logging.info(f"DebugServer listening on {self.host}:{self.port}")

            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()
        except Exception as e:
            logging.error(f"Failed to start DebugServer: {e}")
            self.running = False

    def stop(self) -> None:
        """Stop the debug server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        # Wait for thread? Daemon thread will accept being killed by interpreter exit,
        # but manual join is polite if we have time.

    def _run_server(self) -> None:
        while self.running:
            try:
                # set timeout to allow checking self.running periodically
                if not self.server_socket:
                    break

                self.server_socket.settimeout(1.0)
                try:
                    conn, addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    # Socket closed
                    break

                logging.info(f"Debug client connected from {addr}")
                self._handle_client(conn)
            except Exception as e:
                logging.error(f"Error in debug server loop: {e}")
                if not self.running:
                    break

    def _handle_client(self, conn: socket.socket) -> None:
        with conn:
            buffer = ""
            while self.running:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break

                    buffer += data.decode('utf-8')
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            self._process_message(line.strip(), conn)
                except Exception as e:
                    logging.error(f"Connection error: {e}")
                    break

    def _process_message(self, message: str, conn: socket.socket) -> None:
        try:
            payload = json.loads(message)
            cmd_type = payload.get("type")

            if cmd_type == "event":
                event_data = payload.get("event")
                if event_data:
                    self.command_queue.put(("event", event_data))
                    self._send_response(conn, "ok")
                else:
                    self._send_response(conn, "error", "Missing event data")

            elif cmd_type == "command":
                # General command (resize, screenshot, etc.)
                self.command_queue.put(("command", payload))
                self._send_response(conn, "ok")

            else:
                self._send_response(conn, "error", "Unknown type")

        except json.JSONDecodeError:
            self._send_response(conn, "error", "Invalid JSON")
        except Exception as e:
            self._send_response(conn, "error", str(e))

    def _send_response(self, conn: socket.socket, status: str, message: str = None) -> None:
        resp = {"status": status}
        if message:
            resp["message"] = message
        try:
            conn.sendall((json.dumps(resp) + "\n").encode('utf-8'))
        except Exception:
            pass

    def get_pending_actions(self) -> List[Tuple[str, Any]]:
        """Consume all pending commands/events from the queue."""
        actions = []
        while not self.command_queue.empty():
            actions.append(self.command_queue.get())
        return actions
