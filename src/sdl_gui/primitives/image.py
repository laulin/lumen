from typing import Any, Callable, Dict, List, Tuple, Union

from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive


class Image(BasePrimitive):
    """An image primitive."""

    def __init__(self,
                 source: Union[str, bytes, Callable],
                 x: Union[int, str],
                 y: Union[int, str],
                 width: Union[int, str],
                 height: Union[int, str],
                 scale_mode: str = "fit",
                 padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 margin: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 id: str = None,
                 listen_events: List[str] = None):
        super().__init__(x, y, width, height, padding, margin, id, listen_events)
        self.source = source
        self.scale_mode = scale_mode

    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data for this image."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_IMAGE
        data[core.KEY_SOURCE] = self.source
        if self.scale_mode != "fit":
            data[core.KEY_SCALE_MODE] = self.scale_mode
        return data
