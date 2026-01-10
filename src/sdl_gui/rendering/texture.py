
import ctypes
from typing import Any, Union

import sdl2
import sdl2.ext


class RawTexture(sdl2.ext.Texture):
    """
    A Texture wrapper that can be initialized from an existing SDL_Texture.
    """
    def __init__(self, renderer: Union[sdl2.ext.Renderer, Any], tx: Any):
        # We bypass the standard __init__ since it requires a surface

        self.renderer = renderer
        self.tx = tx

        # Cache size
        w, h = ctypes.c_int(), ctypes.c_int()
        sdl2.SDL_QueryTexture(tx, None, None, ctypes.byref(w), ctypes.byref(h))
        self._size = (w.value, h.value)

    def __del__(self):
        if self.tx:
             sdl2.SDL_DestroyTexture(self.tx)
             self.tx = None
