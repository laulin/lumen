import sdl2
import sdl2.ext
from typing import List, Dict, Any, Tuple
from sdl_gui import core

class Window:
    """SDL Window wrapper that renders a display list."""
    
    def __init__(self, title: str, width: int, height: int):
        sdl2.ext.init()
        self.window = sdl2.ext.Window(title, size=(width, height), flags=sdl2.SDL_WINDOW_RESIZABLE)
        self.renderer = sdl2.ext.Renderer(self.window)
        self.width = width
        self.height = height
        
    def show(self) -> None:
        """Show the window."""
        self.window.show()

    def render(self, display_list: List[Dict[str, Any]]) -> None:
        """Render the display list."""
        self.renderer.clear()
        
        # Determine current window size (in case of resize)
        # For now using initial size or updated size if we tracked resize events, 
        # but simplistic approach: use stored size. 
        # Ideally we'd get window.size, but let's stick to simple property.
        
        root_rect = (0, 0, self.width, self.height)
        
        for item in display_list:
            self._render_item(item, root_rect)
            
        self.renderer.present()
        
    def _resolve_val(self, val: Any, base: int) -> int:
        """Resolve a dimension value (int or percentage string)."""
        if isinstance(val, int):
            return val
        if isinstance(val, str) and val.endswith("%"):
            try:
                pct = float(val[:-1]) / 100.0
                return int(base * pct)
            except ValueError:
                pass
        return 0

    def _resolve_rect(self, rect_data: List[Any], parent_rect: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """Resolve a rect relative to parent."""
        px, py, pw, ph = parent_rect
        rx = self._resolve_val(rect_data[0], pw)
        ry = self._resolve_val(rect_data[1], ph)
        rw = self._resolve_val(rect_data[2], pw)
        rh = self._resolve_val(rect_data[3], ph)
        
        # X and Y are relative to parent origin
        return (px + rx, py + ry, rw, rh)


    def _render_item(self, item: Dict[str, Any], parent_rect: Tuple[int, int, int, int]) -> None:
        """Render a single item recursively."""

        # Resolve current item's rect
        raw_rect = item.get(core.KEY_RECT)
        current_rect = parent_rect
        
        if raw_rect:
            current_rect = self._resolve_rect(raw_rect, parent_rect)

        item_type = item.get(core.KEY_TYPE)
        
        if item_type == core.TYPE_LAYER:
            children = item.get(core.KEY_CHILDREN, [])
            for child in children:
                self._render_item(child, current_rect)
                
        elif item_type == core.TYPE_RECT:
            color = item.get("color", (255, 255, 255, 255))
            if raw_rect: # Only draw if it has a rect
                self.renderer.fill(current_rect, color)

