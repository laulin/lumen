
from typing import Any, Dict, List, Tuple, Union

import sdl2
import sdl2.ext
from sdl2 import sdlgfx

from sdl_gui import core, utils
from sdl_gui.rendering.primitive_renderer import PrimitiveRenderer
from sdl_gui.rendering.texture import RawTexture


class VectorRenderer:
    """
    Handles rendering of vector graphics primitives by creating software surfaces
    and caching them as textures.
    """

    def __init__(self, renderer: sdl2.ext.Renderer, primitive_renderer: PrimitiveRenderer):
        self.renderer = renderer
        self.primitive_renderer = primitive_renderer
        self._vector_cache: Dict[str, sdl2.ext.Texture] = {}

    def clear_cache(self):
        self._vector_cache.clear()

    def render_vector_graphics(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        """Render vector graphics instructions, utilizing caching."""
        x, y, w, h = rect
        if w <= 0 or h <= 0: return

        # Auto-generate cache key from commands hash if not explicitly provided
        cache_key = item.get(core.KEY_CACHE_KEY)
        if not cache_key:
            # Generate key from commands content for auto-caching
            commands = item.get(core.KEY_COMMANDS, [])
            cache_key = hash(str(commands))

        # Include size in cache key since vector graphics are rendered at specific sizes
        full_key = f"vg_{cache_key}_{w}_{h}"
        texture = self._vector_cache.get(full_key)

        if not texture:
             # Create Texture
             texture = self._create_vector_texture(item, w, h)
             if texture:
                 self._vector_cache[full_key] = texture

        if texture:
             self.primitive_renderer.flush()
             self.renderer.copy(texture, dstrect=(x, y, w, h))

    def _create_vector_texture(self, item: Dict[str, Any], w: int, h: int) -> Union[sdl2.ext.Texture, None]:
        if w <= 0 or h <= 0: return None

        # 1. Create Surface
        surface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, w, h, 32, sdl2.SDL_PIXELFORMAT_RGBA8888)
        if not surface: return None

        # 2. Create Software Renderer
        sw_renderer = sdl2.SDL_CreateSoftwareRenderer(surface)
        if not sw_renderer:
            sdl2.SDL_FreeSurface(surface)
            return None

        # 3. Setup Drawing
        sdl2.SDL_SetRenderDrawBlendMode(sw_renderer, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderDrawColor(sw_renderer, 0, 0, 0, 0)
        sdl2.SDL_RenderClear(sw_renderer)

        # 4. Resolve Content Area
        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        pt = utils.resolve_val(raw_padding[0], h)
        pr = utils.resolve_val(raw_padding[1], w)
        pb = utils.resolve_val(raw_padding[2], h)
        pl = utils.resolve_val(raw_padding[3], w)

        content_w = max(0, w - pl - pr)
        content_h = max(0, h - pt - pb)

        # 5. Execute Commands (using AA primitives internally)
        self._execute_vector_commands(
            item.get(core.KEY_COMMANDS, []),
            w, h,
            content_w=content_w, content_h=content_h,
            offset_x=pl, offset_y=pt,
            renderer_override=sw_renderer
        )

        sdl2.SDL_RenderPresent(sw_renderer)

        # 6. Create Texture from Surface
        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer.sdlrenderer, surface)

        # 7. Cleanup
        sdl2.SDL_DestroyRenderer(sw_renderer)
        sdl2.SDL_FreeSurface(surface)

        if texture:
            sdl2.SDL_SetTextureBlendMode(texture, sdl2.SDL_BLENDMODE_BLEND)
            return RawTexture(self.renderer, texture)
        return None

    def _execute_vector_commands(self, commands: List[Dict[str, Any]], w: int, h: int,
                                 content_w: int = None, content_h: int = None,
                                 offset_x: int = 0, offset_y: int = 0,
                                 renderer_override=None, scale_factor: int = 1):
        renderer = renderer_override if renderer_override else self.renderer.sdlrenderer

        cw = content_w if content_w is not None else w
        ch = content_h if content_h is not None else h

        def res_x(val): return utils.resolve_val(val, cw) + offset_x
        def res_y(val): return utils.resolve_val(val, ch) + offset_y
        def res_w(val): return utils.resolve_val(val, cw)
        def res_h(val): return utils.resolve_val(val, ch)
        def res_r(val): return utils.resolve_val(val, min(cw, ch))

        # State
        stroke_color = self._to_sdlgfx_color((255, 255, 255, 255)) # Default white
        fill_color = None
        current_x, current_y = offset_x, offset_y # Start at 0,0 relative to content
        stroke_width = 1 * scale_factor  # Scale stroke width for supersampling

        for cmd in commands:
            ctype = cmd.get(core.CMD_TYPE)

            if ctype == core.CMD_STROKE:
                 c = cmd.get("color", (255, 255, 255, 255))
                 stroke_color = self._to_sdlgfx_color(c)
                 stroke_width = cmd.get("width", 1) * scale_factor

            elif ctype == core.CMD_FILL:
                 c = cmd.get("color")
                 if c:
                     fill_color = self._to_sdlgfx_color(c)
                 else:
                     fill_color = None

            elif ctype == core.CMD_MOVE_TO:
                 current_x = res_x(cmd.get("x", 0))
                 current_y = res_y(cmd.get("y", 0))

            elif ctype == core.CMD_LINE_TO:
                 tx = res_x(cmd.get("x", 0)); ty = res_y(cmd.get("y", 0))
                 if stroke_width <= 1:
                     sdlgfx.aalineColor(renderer, int(current_x), int(current_y), int(tx), int(ty), stroke_color)
                 else:
                     sdlgfx.thickLineColor(renderer, int(current_x), int(current_y), int(tx), int(ty), int(stroke_width), stroke_color)
                 current_x, current_y = tx, ty

            elif ctype == core.CMD_RECT:
                 rx = res_x(cmd.get("x", 0)); ry = res_y(cmd.get("y", 0))
                 rw = res_w(cmd.get("w", 0)); rh = res_h(cmd.get("h", 0))
                 rr = res_r(cmd.get("r", 0))

                 if fill_color is not None:
                     if rr > 0:
                         sdlgfx.roundedBoxColor(renderer, rx, ry, rx+rw-1, ry+rh-1, rr, fill_color)
                     else:
                         sdlgfx.boxColor(renderer, rx, ry, rx+rw-1, ry+rh-1, fill_color)

                 if stroke_width > 0:
                      if rr > 0:
                          sdlgfx.roundedRectangleColor(renderer, rx, ry, rx+rw-1, ry+rh-1, rr, stroke_color)
                      else:
                          x1, y1, x2, y2 = int(rx), int(ry), int(rx+rw-1), int(ry+rh-1)
                          sdlgfx.aalineColor(renderer, x1, y1, x2, y1, stroke_color)  # Top
                          sdlgfx.aalineColor(renderer, x2, y1, x2, y2, stroke_color)  # Right
                          sdlgfx.aalineColor(renderer, x2, y2, x1, y2, stroke_color)  # Bottom
                          sdlgfx.aalineColor(renderer, x1, y2, x1, y1, stroke_color)  # Left

            elif ctype == core.CMD_CIRCLE:
                 cx = res_x(cmd.get("x", 0)); cy = res_y(cmd.get("y", 0)); r = res_r(cmd.get("r", 0))
                 if fill_color is not None:
                      sdlgfx.filledCircleColor(renderer, cx, cy, r, fill_color)
                 if stroke_width > 0:
                      sdlgfx.aacircleColor(renderer, cx, cy, r, stroke_color)

            elif ctype == core.CMD_ARC:
                  cx = res_x(cmd.get("x", 0)); cy = res_y(cmd.get("y", 0)); r = res_r(cmd.get("r", 0))
                  start = cmd.get("start", 0); end = cmd.get("end", 0)
                  sdlgfx.arcColor(renderer, cx, cy, r, start, end, stroke_color)

            elif ctype == core.CMD_PIE:
                  cx = res_x(cmd.get("x", 0)); cy = res_y(cmd.get("y", 0)); r = res_r(cmd.get("r", 0))
                  start = cmd.get("start", 0); end = cmd.get("end", 0)
                  if fill_color is not None:
                      sdlgfx.filledPieColor(renderer, cx, cy, r, start, end, fill_color)
                  if stroke_width > 0:
                      sdlgfx.pieColor(renderer, cx, cy, r, start, end, stroke_color)

    def _to_sdlgfx_color(self, color: Union[Tuple, List]) -> int:
        if isinstance(color, list): color = tuple(color)
        if len(color) == 3: color = (*color, 255)
        r, g, b, a = color
        return (a << 24) | (b << 16) | (g << 8) | r
