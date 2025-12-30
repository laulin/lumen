from typing import Tuple, List, Any, Dict, Union
from sdl_gui import core

class Rectangle:
    """A basic rectangle primitive."""
    
    def __init__(self, x: Union[int, str], y: Union[int, str], width: Union[int, str], height: Union[int, str], color: Tuple[int, int, int, int]):

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data for this rectangle."""
        return {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [self.x, self.y, self.width, self.height],
            "color": self.color
        }
