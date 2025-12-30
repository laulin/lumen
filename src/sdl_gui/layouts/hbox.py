from typing import Dict, Any, List, Union
from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive

class HBox(BasePrimitive):
    """Horizontal Box Layout."""
    
    def __init__(self, x: Union[int, str], y: Union[int, str], width: Union[int, str], height: Union[int, str],
                 padding: tuple = (0, 0, 0, 0), margin: tuple = (0, 0, 0, 0),
                 events: Dict[str, Any] = None):
        super().__init__(x, y, width, height, padding, margin, events)
        self.children: List[Any] = []


    def add_child(self, child: Any) -> None:
        """Add a child to the layout."""
        self.children.append(child)

    def to_data(self) -> Dict[str, Any]:
        """Generate HBox data."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_HBOX
        data[core.KEY_CHILDREN] = [child.to_data() for child in self.children]
        return data
