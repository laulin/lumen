from typing import Any, Dict, List, Union, Optional
from sdl_gui import core
from sdl_gui.primitives.container import Container

class FlexBox(Container):
    """
    Flexbox Layout Container.
    Uses the FlexLayout engine to position children.
    """

    def __init__(self, x: Union[int, str], y: Union[int, str], width: Union[int, str], height: Union[int, str],
                 flex_direction: str = "row",
                 justify_content: str = "flex_start",
                 align_items: str = "stretch",
                 flex_wrap: str = "nowrap",
                 gap: int = 0,
                 padding: tuple = (0, 0, 0, 0), margin: tuple = (0, 0, 0, 0),
                 id: str = None,
                 listen_events: List[str] = None):
        super().__init__(x, y, width, height, padding, margin, id, listen_events)
        self.flex_direction = flex_direction
        self.justify_content = justify_content
        self.align_items = align_items
        self.flex_wrap = flex_wrap
        self.gap = gap
        self.children: List[Any] = []

    def to_data(self) -> Dict[str, Any]:
        """Generate FlexBox data."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_FLEXBOX
        
        data[core.KEY_FLEX_DIRECTION] = self.flex_direction
        data[core.KEY_JUSTIFY_CONTENT] = self.justify_content
        data[core.KEY_ALIGN_ITEMS] = self.align_items
        data[core.KEY_FLEX_WRAP] = self.flex_wrap
        data[core.KEY_GAP] = self.gap
        
        if self.children:
            data[core.KEY_CHILDREN] = [child.to_data() for child in self.children]
        
        return data
