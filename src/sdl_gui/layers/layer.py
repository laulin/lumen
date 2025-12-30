from typing import List, Dict, Any, Union
from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive

class Layer(BasePrimitive):
    """A container layer that manages a list of children elements."""
    
    def __init__(self, x: Union[int, str], y: Union[int, str], 
                 width: Union[int, str], height: Union[int, str],
                 events: Dict[str, Any] = None):
        super().__init__(x, y, width, height, events=events)
        self.children: List[Any] = []


    def add_child(self, child: Any) -> None:
        """Add a child element to the layer."""
        self.children.append(child)

    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data for this layer and its children."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_LAYER
        data[core.KEY_CHILDREN] = [child.to_data() for child in self.children]
        return data

