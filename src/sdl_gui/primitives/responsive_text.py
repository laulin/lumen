from typing import Tuple, List, Any, Dict, Union
from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive

class ResponsiveText(BasePrimitive):
    """A responsive text primitive."""
    
    def __init__(self, x: Union[int, str], y: Union[int, str], width: Union[int, str], height: Union[int, str], 
                 text: str,
                 font: str = None,
                 size: Union[int, str] = 16,
                 color: Tuple[int, int, int, int] = (0, 0, 0, 255),
                 align: str = "left",
                 padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 margin: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 id: str = None,
                 listen_events: List[str] = None):
        super().__init__(x, y, width, height, padding, margin, id, listen_events)
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.align = align

    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data for this text."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_TEXT
        data[core.KEY_TEXT] = self.text
        data[core.KEY_FONT] = self.font
        data[core.KEY_FONT_SIZE] = self.size
        data[core.KEY_COLOR] = self.color
        data[core.KEY_ALIGN] = self.align
        return data
