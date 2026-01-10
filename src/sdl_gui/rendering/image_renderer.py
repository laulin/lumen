
import ctypes
from typing import Any, Callable, Dict, Tuple, Union

import sdl2
import sdl2.ext

from sdl_gui import core
from sdl_gui.rendering.primitive_renderer import PrimitiveRenderer
from sdl_gui.rendering.texture import RawTexture


class ImageRenderer:
    """
    Handles rendering of images, including loading and caching.
    Supports rounded images.
    """

    def __init__(self, renderer: sdl2.ext.Renderer, primitive_renderer: PrimitiveRenderer):
        self.renderer = renderer
        self.primitive_renderer = primitive_renderer
        self._image_cache: Dict[str, sdl2.ext.Texture] = {}

    def clear_cache(self):
        self._image_cache.clear()

    def render_image(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        source = item.get(core.KEY_SOURCE)
        if not source: return

        radius = item.get(core.KEY_RADIUS, 0)
        scale_mode = item.get(core.KEY_SCALE_MODE, "fit")
        item_id = item.get(core.KEY_ID)

        # 1. Get/Load original texture
        orig_cache_key = item_id if item_id else (source if isinstance(source, str) else str(id(source)))
        texture = self._image_cache.get(orig_cache_key)
        if not texture:
            surface = self._load_image_source(source)
            if surface:
                texture = sdl2.ext.Texture(self.renderer, surface)
                sdl2.SDL_FreeSurface(surface)
                self._image_cache[orig_cache_key] = texture
        if not texture: return

        # 2. Calculate dimensions
        img_w, img_h = texture.size
        dest_x, dest_y, dest_w, dest_h = rect
        final_x, final_y, final_w, final_h = dest_x, dest_y, dest_w, dest_h

        if scale_mode == "fit" and img_w > 0 and img_h > 0:
             scale = min(dest_w / img_w, dest_h / img_h)
             final_w = int(img_w * scale); final_h = int(img_h * scale)
             final_x = dest_x + (dest_w - final_w) // 2
             final_y = dest_y + (dest_h - final_h) // 2
        elif scale_mode == "center":
             final_w = img_w; final_h = img_h
             final_x = dest_x + (dest_w - img_w) // 2
             final_y = dest_y + (dest_h - img_h) // 2

        if final_w <= 0 or final_h <= 0: return

        # Ensure primitives are flushed before drawing texture
        self.primitive_renderer.flush()

        # 3. Handle Rounded Corners
        if radius > 0:
            radius = min(radius, final_w // 2, final_h // 2)

        if radius > 0:
            rounded_key = f"rounded_{orig_cache_key}_{final_w}_{final_h}_{radius}"
            rounded_texture = self._image_cache.get(rounded_key)
            if not rounded_texture:
                rounded_texture = self._create_rounded_image_texture(texture, final_w, final_h, radius)
                if rounded_texture:
                    self._image_cache[rounded_key] = rounded_texture

            if rounded_texture:
                self.renderer.copy(rounded_texture, dstrect=(final_x, final_y, final_w, final_h))
                return

        # 4. Standard render
        self.renderer.copy(texture, dstrect=(final_x, final_y, final_w, final_h))

    def _create_rounded_image_texture(self, orig_texture: sdl2.ext.Texture, w: int, h: int, radius: int) -> Union[sdl2.ext.Texture, None]:
        """Create a new texture with image content clipped by rounded corners."""
        sdl_renderer = self.renderer.sdlrenderer

        # Create target texture
        target = sdl2.SDL_CreateTexture(sdl_renderer, sdl2.SDL_PIXELFORMAT_RGBA8888,
                                        sdl2.SDL_TEXTUREACCESS_TARGET, w, h)
        if not target: return None

        sdl2.SDL_SetTextureBlendMode(target, sdl2.SDL_BLENDMODE_BLEND)

        # Save current target and switch
        old_target = sdl2.SDL_GetRenderTarget(sdl_renderer)
        sdl2.SDL_SetRenderTarget(sdl_renderer, target)

        # Clear target (transparent)
        sdl2.SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0, 0)
        sdl2.SDL_RenderClear(sdl_renderer)

        # Draw mask (white rounded box) using PrimitiveRenderer helper directly or local implementation?
        # PrimitiveRenderer has _draw_aa_rounded_box.
        # But _draw_aa_rounded_box uses self.renderer.sdlrenderer.
        # Since we switched render target, self.renderer.sdlrenderer (which is same ptr) works on TARGET.
        self.primitive_renderer._draw_aa_rounded_box((0, 0, w, h), radius, (255, 255, 255, 255))

        old_blend_mode = sdl2.SDL_BlendMode()
        sdl2.SDL_GetTextureBlendMode(orig_texture.tx, ctypes.byref(old_blend_mode))

        sdl2.SDL_SetTextureBlendMode(orig_texture.tx, sdl2.SDL_BLENDMODE_MOD)
        sdl2.SDL_RenderCopy(sdl_renderer, orig_texture.tx, None, sdl2.SDL_Rect(0, 0, w, h))

        # Restore state
        sdl2.SDL_SetTextureBlendMode(orig_texture.tx, old_blend_mode)
        sdl2.SDL_SetRenderTarget(sdl_renderer, old_target)

        return RawTexture(self.renderer, target)

    def _load_image_source(self, source: Union[str, bytes, Callable]) -> Any:
        try: import sdl2.sdlimage as img
        except ImportError: return None

        if isinstance(source, str):
            return img.IMG_Load(source.encode('utf-8'))
        elif isinstance(source, bytes):
            rw = sdl2.SDL_RWFromConstMem(source, len(source))
            return img.IMG_Load_RW(rw, 1)
        elif callable(source):
            return None
        return None

# Duplicate RawTexture here or import?
# RawTexture is in renderer.py.
# Better to extract RawTexture to a separate file `src/sdl_gui/texture.py` or similar to avoid circular imports
# whenever ImageRenderer is imported by Renderer.
# PrimitiveRenderer is fine.
# ImageRenderer needs RawTexture.
# I will define RawTexture in `src/sdl_gui/rendering/common.py` or just inside ImageRenderer if only used there?
# No, RawTexture was a helper class. It might be useful elsewhere.
# But for now I will define it here or import if I can avoid circular dep.
# Renderer imports ImageRenderer. ImageRenderer imports Renderer? No.
# ImageRenderer does NOT import Renderer. It just types `sdl2.ext.Renderer`.
# But `RawTexture` was in `renderer.py`.
# I should move `RawTexture` to `src/sdl_gui/rendering/texture.py`.


