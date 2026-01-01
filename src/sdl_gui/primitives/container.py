from typing import Any

from sdl_gui import context
from sdl_gui.primitives.base import BasePrimitive


class Container(BasePrimitive):
    """
    A mixin/base class for primitives that can contain other children.
    Implements context manager support to automatically add children
    created within its context.
    """

    def __enter__(self):
        context.push_parent(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        context.pop_parent()

    def add_child(self, child: Any) -> None:
        """
        Add a child to this container. 
        Subclasses should implement or override this if they have specific logic,
        but we provide a default that assumes a `children` list attribute exists.
        """
        if hasattr(self, 'children') and isinstance(self.children, list):
            self.children.append(child)
        else:
            raise NotImplementedError(f"{type(self).__name__} does not support adding children or lacks a 'children' list.")
