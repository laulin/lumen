from typing import Any, Dict, List, Tuple, Union

from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive


class Rectangle(BasePrimitive):
    """A basic rectangle primitive."""


    def __init__(self, x: Union[int, str], y: Union[int, str], width: Union[int, str], height: Union[int, str],
                 color: Tuple[int, int, int, int],
                 radius: int = 0,
                 border_color: Tuple[int, int, int, int] = None,
                 border_width: int = 0,
                 padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 margin: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 id: str = None,
                 listen_events: List[str] = None):
        super().__init__(x, y, width, height, padding, margin, id, listen_events)
        self.color = color
        self.radius = radius
        self.border_color = border_color
        self.border_width = border_width

    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data for this rectangle."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_RECT
        data["color"] = self.color
        if self.radius > 0:
            data[core.KEY_RADIUS] = self.radius
        if self.border_color and self.border_width > 0:
            data[core.KEY_BORDER_COLOR] = self.border_color
            data[core.KEY_BORDER_WIDTH] = self.border_width
        return data

