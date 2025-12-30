from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Union
from sdl_gui import core

class BasePrimitive(ABC):
    """Abstract base class for all display primitives."""

    def __init__(self, 
                 x: Union[int, str], 
                 y: Union[int, str], 
                 width: Union[int, str], 
                 height: Union[int, str],
                 padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 margin: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 events: Dict[str, Any] = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.padding = padding
        self.margin = margin
        self.events = events or {}

    @abstractmethod
    def to_data(self) -> Dict[str, Any]:
        """Generate common data fields."""
        return {
            core.KEY_RECT: [self.x, self.y, self.width, self.height],
            core.KEY_PADDING: self.padding,
            core.KEY_MARGIN: self.margin,
            core.KEY_EVENTS: self.events
        }

