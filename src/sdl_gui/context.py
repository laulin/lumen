from threading import local
from typing import Any, List, Optional

# Thread-local storage for the context stack
_thread_local = local()

def _get_stack() -> List[Any]:
    if not hasattr(_thread_local, "stack"):
        _thread_local.stack = []
    return _thread_local.stack

def push_parent(parent: Any) -> None:
    """Push a parent container onto the stack."""
    stack = _get_stack()
    stack.append(parent)

def pop_parent() -> Optional[Any]:
    """Pop the last parent from the stack."""
    stack = _get_stack()
    if stack:
        return stack.pop()
    return None

def get_current_parent() -> Optional[Any]:
    """Get the current active parent container."""
    stack = _get_stack()
    if stack:
        return stack[-1]
    return None
