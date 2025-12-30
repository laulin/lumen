from typing import Tuple, List, Any, Dict, Union
from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive

class Rectangle(BasePrimitive):
    """A basic rectangle primitive."""
    
    def __init__(self, x: Union[int, str], y: Union[int, str], width: Union[int, str], height: Union[int, str], 
                 color: Tuple[int, int, int, int],
                 padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 margin: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 events: Dict[str, Any] = None):
        super().__init__(x, y, width, height, padding, margin, events)
        self.color = color


    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data for this rectangle."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_RECT
        data["color"] = self.color
        return data

