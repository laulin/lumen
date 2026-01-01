from typing import Any, Dict, List, Union

from sdl_gui import core
from sdl_gui.layers.layer import Layer


class ScrollableLayer(Layer):
    """A layer that can be scrolled."""

    def __init__(self, x: Union[int, str], y: Union[int, str],
                 width: Union[int, str], height: Union[int, str],
                 scroll_y: int = 0,
                 content_height: int = 0,
                 id: str = None,
                 listen_events: List[str] = None):
        super().__init__(x, y, width, height, id=id, listen_events=listen_events)
        self.scroll_y = scroll_y
        self.content_height = content_height

    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_SCROLLABLE_LAYER
        data[core.KEY_SCROLL_Y] = self.scroll_y
        data[core.KEY_CONTENT_HEIGHT] = self.content_height
        return data
