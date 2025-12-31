from abc import ABC, abstractmethod
from typing import Dict, Any, Union, Tuple, List
from sdl_gui import core, context

class BasePrimitive(ABC):
    """Abstract base class for all display primitives."""

    def __init__(self, 
                 x: Union[int, str], 
                 y: Union[int, str], 
                 width: Union[int, str], 
                 height: Union[int, str],
                 padding: Union[int, str, Tuple[int, int, int, int], List[int]] = (0, 0, 0, 0),
                 margin: Union[int, str, Tuple[int, int, int, int], List[int]] = (0, 0, 0, 0),
                 id: str = None,
                 listen_events: List[str] = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.padding = self._normalize_spacing(padding)
        self.margin = self._normalize_spacing(margin)
        self.id = id
        self.listen_events = listen_events or []
        self.extra: Dict[str, Any] = {}
        
        # Implicit parenting
        parent = context.get_current_parent()
        if parent and hasattr(parent, 'add_child'):
            parent.add_child(self)

    def __enter__(self):
        """Default enter for primitives that are not containers: just return self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Default exit: do nothing."""
        pass

    def _normalize_spacing(self, val: Union[int, str, Tuple, List]) -> Tuple[Any, Any, Any, Any]:
        """Normalize spacing value to (top, right, bottom, left)."""
        if isinstance(val, (int, str)):
            return (val, val, val, val)
        elif isinstance(val, (tuple, list)):
            if len(val) == 4:
                return tuple(val)
            elif len(val) == 2:
                # Top/Bottom, Right/Left
                return (val[0], val[1], val[0], val[1])
            elif len(val) == 1:
                return (val[0], val[0], val[0], val[0])
        return (0, 0, 0, 0)

    @abstractmethod
    def to_data(self) -> Dict[str, Any]:
        """Generate common data fields."""
        data = {
            core.KEY_RECT: [self.x, self.y, self.width, self.height],
            core.KEY_PADDING: self.padding,
            core.KEY_MARGIN: self.margin
        }
        if self.id:
            data[core.KEY_ID] = self.id
        if self.listen_events:
            data[core.KEY_LISTEN_EVENTS] = self.listen_events
        
        # Merge extra properties (e.g. background color)
        data.update(self.extra)
        
        return data

    
    # Registry of allowed style properties to validation/mapping logic if needed
    # For now, just a set of allowed names.
    ALLOWED_PROPERTIES = {
        'radius', 
        'border_width', 
        'border_color', 
        'color', 
        'background_color', # Maps to color
        'margin',
        'padding'
    }

    def __getattr__(self, name: str):
        """
        Generic setter mechanism.
        Intercepts calls to set_xxx and validates xxx against ALLOWED_PROPERTIES.
        """
        if name.startswith("set_"):
            prop_name = name[4:]
            
            if prop_name in self.ALLOWED_PROPERTIES:
                # Helper to handle the actual setting
                def setter(*args):
                    key = prop_name
                    # Map Alias
                    if prop_name == 'background_color':
                        key = 'color'
                    
                    # Determine value
                    if len(args) == 1:
                        val = args[0]
                    else:
                        val = args # tuple
                    
                    self.extra[key] = val
                    return self
                    
                return setter
            else:
                 raise AttributeError(f"Property '{prop_name}' is not allowed or does not exist.")
        
        # Default behavior for other attributes
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


