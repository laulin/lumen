from typing import List, Dict, Any, Union
from sdl_gui import core

class Layer:
    """A container layer that manages a list of children elements."""
    
    def __init__(self, x: Union[int, str], y: Union[int, str], width: Union[int, str], height: Union[int, str]):

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.children: List[Any] = []

    def add_child(self, child: Any) -> None:
        """Add a child element to the layer."""
        self.children.append(child)

    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data for this layer and its children."""
        children_data = [child.to_data() for child in self.children]
        
        return {
            core.KEY_TYPE: core.TYPE_LAYER,
            core.KEY_RECT: [self.x, self.y, self.width, self.height],
            core.KEY_CHILDREN: children_data
        }
