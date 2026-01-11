
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
        # Use _tx to match the parent class property
        self._tx = tx
        
        # Initialize _renderer_ref to match parent class expectations
        if isinstance(renderer, sdl2.ext.Renderer):
            self._renderer_ref = renderer._renderer_ref
        else:
            # Fallback: wrap the renderer reference
            self._renderer_ref = [renderer.sdlrenderer if hasattr(renderer, 'sdlrenderer') else renderer]

        # Cache size
        w, h = ctypes.c_int(), ctypes.c_int()
        sdl2.SDL_QueryTexture(tx, None, None, ctypes.byref(w), ctypes.byref(h))
        self._size = (w.value, h.value)

    def __del__(self):
        if hasattr(self, '_tx') and self._tx:
            sdl2.SDL_DestroyTexture(self._tx)
            self._tx = None
