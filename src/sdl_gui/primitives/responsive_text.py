from typing import Any, Dict, List, Tuple, Union

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
                 wrap: bool = True,
                 ellipsis: bool = True,
                 markup: bool = True,
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
        self.wrap = wrap
        self.ellipsis = ellipsis
        self.markup = markup

    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data for this text."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_TEXT
        data[core.KEY_TEXT] = self.text
        data[core.KEY_FONT] = self.font
        data[core.KEY_FONT_SIZE] = self.size
        data[core.KEY_COLOR] = self.color
        data[core.KEY_ALIGN] = self.align
        data[core.KEY_WRAP] = self.wrap
        data[core.KEY_ELLIPSIS] = self.ellipsis
        data[core.KEY_MARKUP] = self.markup
        return data
