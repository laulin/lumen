from abc import ABC, abstractmethod
from typing import Dict, Any, Union, Tuple, List
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
                 id: str = None,
                 listen_events: List[str] = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.padding = padding
        self.margin = margin
        self.id = id
        self.listen_events = listen_events or []

    @abstractmethod
    def to_data(self) -> Dict[str, Any]:
        """Generate common data fields."""
        data = {
            core.KEY_RECT: [self.x, self.y, self.width, self.height],
            core.KEY_PADDING: self.padding,
            core.KEY_MARGIN: self.margin
        }
        if self.id:
            data[core.KEY_ID] = self.id
        if self.listen_events:
            data[core.KEY_LISTEN_EVENTS] = self.listen_events
        return data


