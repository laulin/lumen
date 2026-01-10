
from typing import Union

def resolve_val(val: Union[int, float, str], parent_len: int) -> int:
    """
    Resolve a value that might be a percentage or pixel string to an integer.
    
    Args:
        val: The value to resolve (int, float, or string like "50%", "10px").
        parent_len: The length of the parent container (for percentages).
        
    Returns:
        The resolved integer value.
    """
    if isinstance(val, (int, float)):
        return int(val)
    
    if isinstance(val, str):
        if val.endswith("%"):
            try:
                pct = float(val[:-1])
                return int((pct / 100.0) * parent_len)
            except ValueError:
                return 0
        elif val.endswith("px"):
            try:
                return int(val[:-2])
            except ValueError:
                return 0
        else:
            try:
                return int(val)
            except ValueError:
                return 0
                
    return 0
