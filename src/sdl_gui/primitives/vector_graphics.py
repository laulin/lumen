from typing import Any, Dict, List, Tuple, Union, Optional
from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive

class VectorGraphics(BasePrimitive):
    """
    A primitive for drawing vector graphics.
    Uses a command list to record drawing operations which are then executed by the renderer.
    Supports caching via a unique cache_key to avoid re-drawing static content.
    """
    
    def __init__(self, x: Union[int, str], y: Union[int, str], 
                 width: Union[int, str], height: Union[int, str],
                 padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 margin: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 id: str = None,
                 cache_key: str = None,
                 listen_events: List[str] = None):
        super().__init__(x, y, width, height, padding, margin, id, listen_events)
        self.commands: List[Dict[str, Any]] = []
        self._custom_cache_key = cache_key
        
    def set_cache_key(self, key: str):
        """Set a custom cache key. If set, renderer uses this to cache the texture."""
        self._custom_cache_key = key
        return self
        
    def clear(self):
        """Clear all drawing commands."""
        self.commands = []
        self.commands.append({core.CMD_TYPE: core.CMD_CLEAR})
        return self

    def move_to(self, x: Union[int, str], y: Union[int, str]):
        self.commands.append({core.CMD_TYPE: core.CMD_MOVE_TO, "x": x, "y": y})
        return self

    def line_to(self, x: Union[int, str], y: Union[int, str]):
        self.commands.append({core.CMD_TYPE: core.CMD_LINE_TO, "x": x, "y": y})
        return self

    def curve_to(self, cx1: Union[int, str], cy1: Union[int, str], cx2: Union[int, str], cy2: Union[int, str], x: Union[int, str], y: Union[int, str]):
        """Cubic bezier curve."""
        self.commands.append({
            core.CMD_TYPE: core.CMD_CURVE_TO, 
            "cx1": cx1, "cy1": cy1, 
            "cx2": cx2, "cy2": cy2, 
            "x": x, "y": y
        })
        return self

    def arc(self, x: Union[int, str], y: Union[int, str], r: Union[int, str], start: int, end: int):
        self.commands.append({
            core.CMD_TYPE: core.CMD_ARC,
            "x": x, "y": y, "r": r,
            "start": start, "end": end
        })
        return self
        
    def circle(self, x: Union[int, str], y: Union[int, str], r: Union[int, str]):
        self.commands.append({core.CMD_TYPE: core.CMD_CIRCLE, "x": x, "y": y, "r": r})
        return self

    def pie(self, x: Union[int, str], y: Union[int, str], r: Union[int, str], start: int, end: int):
        self.commands.append({
            core.CMD_TYPE: core.CMD_PIE,
            "x": x, "y": y, "r": r,
            "start": start, "end": end
        })
        return self

    def rect(self, x: Union[int, str], y: Union[int, str], w: Union[int, str], h: Union[int, str], r: Union[int, str] = 0):
        self.commands.append({
            core.CMD_TYPE: core.CMD_RECT,
            "x": x, "y": y, "w": w, "h": h, "r": r
        })
        return self

    def stroke(self, color: Tuple[int, int, int, int], width: int = 1):
        """Set stroke color and width for subsequent operations (or current path if applicable in future)."""
        # Ensure color is 4 elements
        if len(color) == 3: color = (*color, 255)
        self.commands.append({
            core.CMD_TYPE: core.CMD_STROKE,
            "color": color,
            "width": width
        })
        return self

    def fill(self, color: Tuple[int, int, int, int]):
        """Fill current path or shapes. (Note: mostly implements primitive fills like filled circle/rect for now)"""
        if len(color) == 3: color = (*color, 255)
        self.commands.append({
            core.CMD_TYPE: core.CMD_FILL,
            "color": color
        })
        return self

    def to_data(self) -> Dict[str, Any]:
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_VECTOR_GRAPHICS
        data[core.KEY_COMMANDS] = self.commands
        # If user didn't provide a key, we might generate one or leave it None (no caching)
        # For performance, auto-generation based on commands hash is expensive. 
        # Better to rely on user or object ID if content is static?
        # If content changes, ID is same but content diff. 
        # So explicit key is safer.
        if self._custom_cache_key:
            data[core.KEY_CACHE_KEY] = self._custom_cache_key
        return data
