from dataclasses import dataclass
from typing import Union, Optional
from sdl_gui.layout_engine.definitions import FlexDirection, JustifyContent, AlignItems, FlexWrap

@dataclass
class FlexStyle:
    direction: FlexDirection = FlexDirection.ROW
    justify_content: JustifyContent = JustifyContent.FLEX_START
    align_items: AlignItems = AlignItems.STRETCH
    wrap: FlexWrap = FlexWrap.NOWRAP
    gap: int = 0
    
    # Item properties
    grow: float = 0.0
    shrink: float = 1.0
    basis: Union[int, str] = "auto"
    
    # Box Model for layout calculations
    width: Union[int, str, None] = None
    height: Union[int, str, None] = None
    margin: tuple = (0, 0, 0, 0) # top, right, bottom, left
    padding: tuple = (0, 0, 0, 0)
