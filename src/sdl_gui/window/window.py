import sdl2
import sdl2.ext
from typing import List, Dict, Any
from sdl_gui import core

class Window:
    """SDL Window wrapper that renders a display list."""
    
    def __init__(self, title: str, width: int, height: int):
        sdl2.ext.init()
        self.window = sdl2.ext.Window(title, size=(width, height), flags=sdl2.SDL_WINDOW_RESIZABLE)
        self.renderer = sdl2.ext.Renderer(self.window)
        
    def show(self) -> None:
        """Show the window."""
        self.window.show()

    def render(self, display_list: List[Dict[str, Any]]) -> None:
        """Render the display list."""
        self.renderer.clear()
        
        for item in display_list:
            self._render_item(item)
            
        self.renderer.present()
        
    def _render_item(self, item: Dict[str, Any]) -> None:
        """Render a single item recursively."""
        item_type = item.get(core.KEY_TYPE)
        
        if item_type == core.TYPE_LAYER:
            children = item.get(core.KEY_CHILDREN, [])
            for child in children:
                self._render_item(child)
                
        elif item_type == core.TYPE_RECT:
            rect = item.get(core.KEY_RECT)
            color = item.get("color", (255, 255, 255, 255))
            if rect:
                self.renderer.fill(rect, color)
