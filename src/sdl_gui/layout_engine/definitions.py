from enum import Enum

class FlexDirection(Enum):
    ROW = "row"
    ROW_REVERSE = "row_reverse"
    COLUMN = "column"
    COLUMN_REVERSE = "column_reverse"

class JustifyContent(Enum):
    FLEX_START = "flex_start"
    FLEX_END = "flex_end"
    CENTER = "center"
    SPACE_BETWEEN = "space_between"
    SPACE_AROUND = "space_around"
    SPACE_EVENLY = "space_evenly"

class AlignItems(Enum):
    FLEX_START = "flex_start"
    FLEX_END = "flex_end"
    CENTER = "center"
    STRETCH = "stretch"
    BASELINE = "baseline"

class FlexWrap(Enum):
    NOWRAP = "nowrap"
    WRAP = "wrap"
    WRAP_REVERSE = "wrap_reverse"
