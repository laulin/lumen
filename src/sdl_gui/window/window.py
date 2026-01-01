
import sdl2
import sdl2.ext
import ctypes
from typing import List, Dict, Any, Tuple
from sdl_gui import core, context
from sdl_gui.window.renderer import Renderer
from sdl_gui.window.debug import Debug

class Window:
    """SDL Window wrapper that delegates rendering and debug to sub-components."""
    
    def __init__(self, title: str, width: int, height: int, debug: bool = False, renderer_flags: int = sdl2.SDL_RENDERER_ACCELERATED):
        sdl2.ext.init()
        
        self.window = sdl2.ext.Window(title, size=(width, height), flags=sdl2.SDL_WINDOW_RESIZABLE)
        
        # Sub-components
        self.renderer = Renderer(self.window, flags=renderer_flags)
        self.debug_system = Debug(enabled=debug)
        
        # State
        self.width = width
        self.height = height

    def __enter__(self):
        """Enter context: return self and potentially set self as a context root."""      
        context.push_parent(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        context.pop_parent()

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

    def render(self, display_list: List[Dict[str, Any]]) -> None:
        """Render the display list."""
        self.renderer.clear()
        
        # Render main content
        self.renderer.render_list(display_list)
        
        # Update and Render Debug
        self.debug_system.update()
        self.debug_system.render(self.renderer)

        self.renderer.present()

    def get_ui_events(self) -> List[Dict[str, Any]]:
        """
        Process SDL events and translate them into UI events based on hit tests.
        Returns a list of high-level UI events (e.g. {'type': 'click', 'target': 'id'}).
        """
        sdl_events = sdl2.ext.get_events()
        ui_events = []
        
        for event in sdl_events:
            # Handle Quit
            if event.type == sdl2.SDL_QUIT:
                ui_events.append({"type": core.EVENT_QUIT})

            # Handle Scroll (Mouse Wheel)
            if event.type == sdl2.SDL_MOUSEWHEEL:
                x, y = ctypes.c_int(0), ctypes.c_int(0)
                sdl2.mouse.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
                mx, my = x.value, y.value
                
                scroll_target = self._find_hit(mx, my, core.EVENT_SCROLL)
                if scroll_target:
                    dy = event.wheel.y
                    # Standard behavior: Wheel UP (pos) -> Move content DOWN (pos delta for logic usually? depends on handler)
                    # We pass the delta from SDL.
                    ui_events.append({
                        "type": core.EVENT_SCROLL,
                        "target": scroll_target.get(core.KEY_ID),
                        "delta": dy,
                        "current_scroll_y": scroll_target.get(core.KEY_SCROLL_Y, 0)
                    })

            # Handle Click
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                mx, my = event.button.x, event.button.y
                clicked_item = self._find_hit(mx, my, core.EVENT_CLICK)
                
                if clicked_item:
                    if clicked_item.get("type") == "link":
                         ui_events.append({
                             "type": core.EVENT_LINK_CLICK,
                             "target": clicked_item.get("target")
                         })
                    else:
                        item_id = clicked_item.get(core.KEY_ID)
                        if item_id:
                            ui_events.append({
                                "type": core.EVENT_CLICK,
                                "target": item_id
                            })

        return ui_events

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
