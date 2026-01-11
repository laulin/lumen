
import ctypes
from typing import Any, Dict, List

import sdl2
import sdl2.ext

from sdl_gui import context, core
from sdl_gui.debug.server import DebugServer
from sdl_gui.window.debug import Debug
from sdl_gui.window.renderer import Renderer


class Window:
    """SDL Window wrapper that delegates rendering and debug to sub-components."""

    def __init__(self, title: str, width: int, height: int, debug: bool = False, renderer_flags: int = sdl2.SDL_RENDERER_ACCELERATED):
        sdl2.ext.init()

        self.window = sdl2.ext.Window(title, size=(width, height), flags=sdl2.SDL_WINDOW_RESIZABLE)

        # Sub-components
        self.renderer = Renderer(self.window, flags=renderer_flags)
        self.debug_system = Debug(enabled=debug)

        # Debug Server
        self.debug_server: DebugServer = None
        if debug:
            self.debug_server = DebugServer()
            self.debug_server.display_list_provider = self.renderer.get_last_display_list
            self.debug_server.start()

        # State
        self.width = width
        self.height = height
        self.focused_element_id = None
        self.mouse_capture_id = None

        sdl2.SDL_StartTextInput()

    def __enter__(self):
        """Enter context: return self and potentially set self as a context root."""
        context.push_parent(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        context.pop_parent()

    def close(self) -> None:
        """Clean up SDL resources and quit SDL."""
        # Stop debug server first
        if self.debug_server:
            self.debug_server.stop()
            self.debug_server = None

        # Clean up renderer resources
        if self.renderer:
            self.renderer.destroy()
            self.renderer = None

        # Destroy window
        if self.window:
            sdl2.SDL_DestroyWindow(self.window.window)
            self.window = None

        # Quit SDL
        sdl2.ext.quit()

    def add_child(self, child: Any) -> None:
        """Allow adding children directly to window (e.g. for implicit context)."""
        if not hasattr(self, 'root_children'):
            self.root_children = []
        self.root_children.append(child)

    def get_root_display_list(self) -> List[Dict[str, Any]]:
        """Helper to get data from root children if used in retained mode way."""
        if hasattr(self, 'root_children'):
            return [child.to_data() for child in self.root_children]
        return []

    def show(self):
        """Show the window."""
        self.window.show()

    def save_screenshot(self, filename: str) -> None:
        """Save the current window content to a BMP file."""
        self.renderer.save_screenshot(filename)

    def measure_text_width(self, text: str, font: str = None, size: int = 16) -> int:
        """Helper to measure text width, used for input processing."""
        return self.renderer.measure_text_width(text, font, size)

    def render(self, display_list: List[Dict[str, Any]], force_full: bool = False) -> None:
        """
        Render the display list.
        
        Args:
            display_list: The list of display items to render.
            force_full: If True, force a full render ignoring incremental mode.
        """
        # Always do full clear - render_list handles partial clearing internally
        self.renderer.clear()

        # Render main content
        self.renderer.render_list(display_list, force_full=force_full)

        # Update and Render Debug
        self.debug_system.update()
        self.debug_system.render(self.renderer)

        self.renderer.present()

    def get_ui_events(self) -> List[Dict[str, Any]]:
        """
        Process SDL events and translate them into UI events based on hit tests.
        Returns a list of high-level UI events.
        """
        sdl_events = sdl2.ext.get_events()
        ui_events = []

        # Always emit Tick
        ui_events.append({"type": core.EVENT_TICK, "ticks": sdl2.SDL_GetTicks()})

        # Process Debug Server Actions
        if self.debug_server:
            for action_type, data in self.debug_server.get_pending_actions():
                if action_type == "event":
                    ui_events.append(data)
                elif action_type == "get_pixel":
                    # data is (x, y, res_queue)
                    x, y, res_queue = data
                    try:
                        color = self.renderer.get_pixel(x, y)
                        res_queue.put(color)
                    except Exception as e:
                        res_queue.put(e)
                elif action_type == "benchmark":
                    # data is (frames, res_queue)
                    frames, res_queue = data
                    try:
                        result = self._run_benchmark(frames)
                        res_queue.put(result)
                    except Exception as e:
                        res_queue.put(e)
                elif action_type == "get_perf_stats":
                    res_queue = data
                    try:
                        stats = self.renderer.get_perf_stats()
                        res_queue.put(stats)
                    except Exception as e:
                        res_queue.put(e)
                elif action_type == "command":
                    val = data.get("action")
                    if val == "quit":
                        ui_events.append({"type": core.EVENT_QUIT})
                    else:
                        self._handle_debug_command(data, ui_events)

        for event in sdl_events:
            # Handle Quit
            if event.type == sdl2.SDL_QUIT:
                ui_events.append({"type": core.EVENT_QUIT})

            # Handle Scroll
            elif event.type == sdl2.SDL_MOUSEWHEEL:
                self._handle_scroll(event, ui_events)

            # Handle Click (Down)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                self._handle_click(event, ui_events)

            # Handle Mouse Up
            elif event.type == sdl2.SDL_MOUSEBUTTONUP:
                self._handle_mouse_up(event, ui_events)

            # Handle Mouse Motion
            elif event.type == sdl2.SDL_MOUSEMOTION:
                self._handle_mouse_motion(event, ui_events)

            # Handle Text Input
            elif event.type == sdl2.SDL_TEXTINPUT:
                if self.focused_element_id:
                     ui_events.append({
                         "type": core.EVENT_TEXT_INPUT,
                         "target": self.focused_element_id,
                         "text": event.text.text.decode('utf-8')
                     })

            # Handle Key Down
            elif event.type == sdl2.SDL_KEYDOWN:
                if self.focused_element_id:
                    ui_events.append({
                        "type": core.EVENT_KEY_DOWN,
                        "target": self.focused_element_id,
                        "key_sym": event.key.keysym.sym,
                        "mod": event.key.keysym.mod
                    })

        return ui_events



    def _handle_scroll(self, event, ui_events):
        x, y = ctypes.c_int(0), ctypes.c_int(0)
        sdl2.mouse.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
        mx, my = x.value, y.value
        self._process_scroll(mx, my, event.wheel.y, ui_events)

    def _process_scroll(self, mx, my, dy, ui_events):
        scroll_target = self._find_hit(mx, my, core.EVENT_SCROLL)
        if scroll_target:
            ui_events.append({
                "type": core.EVENT_SCROLL,
                "target": scroll_target.get(core.KEY_ID),
                "delta": dy,
                "current_scroll_y": scroll_target.get(core.KEY_SCROLL_Y, 0)
            })

    def _handle_click(self, event, ui_events):
        mx, my = event.button.x, event.button.y
        self._process_mouse_down(mx, my, ui_events)

    def _process_mouse_down(self, mx, my, ui_events):
        # Check for focusable item first (Input)
        # We check if we clicked on something that listens to FOCUS
        focus_target = self._find_hit(mx, my, core.EVENT_FOCUS)
        new_focus_id = focus_target.get(core.KEY_ID) if focus_target else None

        if new_focus_id != self.focused_element_id:
            # Blur old
            if self.focused_element_id:
                ui_events.append({"type": core.EVENT_BLUR, "target": self.focused_element_id})
            # Focus new
            if new_focus_id:
                ui_events.append({"type": core.EVENT_FOCUS, "target": new_focus_id})
            self.focused_element_id = new_focus_id

        # Standard Click Handling
        clicked_item = self._find_hit(mx, my, core.EVENT_CLICK)

        # Capture Mouse
        self.mouse_capture_id = None
        if clicked_item:
            self.mouse_capture_id = clicked_item.get(core.KEY_ID)

        if clicked_item:
            if clicked_item.get("type") == "link":
                 ui_events.append({
                     "type": core.EVENT_LINK_CLICK,
                     "target": clicked_item.get("target")
                 })
            else:
                item_id = clicked_item.get(core.KEY_ID)
                if item_id:
                    # Calculate local X/Y for Input cursor positioning
                    rect = self._get_item_rect(clicked_item)
                    local_x = mx - rect[0] if rect else 0
                    local_y = my - rect[1] if rect else 0

                    ui_events.append({
                        "type": core.EVENT_CLICK,
                        "target": item_id,
                        "local_x": local_x,
                        "local_y": local_y
                    })

    def _handle_mouse_up(self, event, ui_events):
        mx, my = event.button.x, event.button.y
        self._process_mouse_up(mx, my, ui_events)

    def _process_mouse_up(self, mx, my, ui_events):
        target_id = None
        item = None

        if self.mouse_capture_id:
            target_id = self.mouse_capture_id
            item, rect = self._find_item_by_id(target_id)

        if target_id and item:
            rect = self._get_item_rect(item)
            local_x = mx - rect[0] if rect else 0
            local_y = my - rect[1] if rect else 0

            ui_events.append({
                "type": core.EVENT_MOUSE_UP,
                "target": target_id,
                "local_x": local_x,
                "local_y": local_y
            })

        self.mouse_capture_id = None

    def _handle_mouse_motion(self, event, ui_events):
        mx, my = event.motion.x, event.motion.y
        self._process_mouse_motion(mx, my, ui_events)

    def _process_mouse_motion(self, mx, my, ui_events):
        target_id = None
        item = None

        if self.mouse_capture_id:
            target_id = self.mouse_capture_id
            item, rect = self._find_item_by_id(target_id)

        if target_id and item:
             rect = self._get_item_rect(item)
             local_x = mx - rect[0] if rect else 0
             local_y = my - rect[1] if rect else 0

             ui_events.append({
                 "type": core.EVENT_MOUSE_MOTION,
                 "target": target_id,
                 "local_x": local_x,
                 "local_y": local_y
             })

    def _find_item_by_id(self, target_id):
        for r, i in self.renderer.get_hit_list():
            if i.get(core.KEY_ID) == target_id:
                return i, r
        return None, None

    def _get_item_rect(self, item):
         # Helper to find rect of item from hit list (a bit inefficient but works)
         for r, i in self.renderer.get_hit_list():
             if i is item: return r
         return None

    def _find_hit(self, mx: int, my: int, required_event: str) -> Dict[str, Any]:
        """
        Find the top-most item at (mx, my) that listens to required_event.
        Returns None if no listening item is found.
        """
        hit_list = self.renderer.get_hit_list()
        # Iterate in reverse to find top-most element first
        for rect, item in reversed(hit_list):
            x, y, w, h = rect
            if x <= mx < x + w and y <= my < y + h:
                listen_events = item.get(core.KEY_LISTEN_EVENTS, [])
                if required_event in listen_events:
                    return item
        return None

    def _handle_debug_command(self, data: Dict[str, Any], ui_events: List[Dict[str, Any]]) -> None:
        """Handle debug commands that affect the window state."""
        action = data.get("action")
        if action == "resize":
             w = data.get("width")
             h = data.get("height")
             if w and h:
                 self.window.size = (w, h)
                 self.width = w; self.height = h
        elif action == "screenshot":
             filename = data.get("filename", "debug_screenshot.bmp")
             self.save_screenshot(filename)
        elif action == "simulate_click":
             x, y = data.get("x", 0), data.get("y", 0)
             self._process_mouse_down(x, y, ui_events)
             self.mouse_capture_id = None # Check for click release usually?
             # Simulating a full click usually involves down then up.
             # For now just down is what starts interactions often.
             # Better: simulate_mouse_down, simulate_mouse_up
        elif action == "mouse_down":
             self._process_mouse_down(data.get("x",0), data.get("y",0), ui_events)
        elif action == "mouse_up":
             self._process_mouse_up(data.get("x",0), data.get("y",0), ui_events)
        elif action == "mouse_move":
             self._process_mouse_motion(data.get("x",0), data.get("y",0), ui_events)

    def _run_benchmark(self, frames: int) -> Dict[str, Any]:
        """
        Run a benchmark by rendering the current display list multiple times.
        
        Args:
            frames: Number of frames to render.
            
        Returns:
            Dict with benchmark results.
        """
        import time
        
        # Enable profiling
        self.renderer.enable_profiling(True)
        
        # Get last display list for repeated rendering
        display_list = self.renderer.get_last_display_list()
        
        # Run frames
        start_time = time.perf_counter()
        for _ in range(frames):
            self.render(display_list)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        
        # Get perf stats
        perf_stats = self.renderer.get_perf_stats()
        
        # Disable profiling
        self.renderer.enable_profiling(False)
        
        return {
            "frames": frames,
            "total_time_ms": total_time * 1000,
            "avg_frame_ms": (total_time / frames) * 1000 if frames > 0 else 0,
            "fps": frames / total_time if total_time > 0 else 0,
            "perf_stats": perf_stats
        }
