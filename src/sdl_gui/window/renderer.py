
import ctypes
import threading
from typing import Any, Callable, Dict, List, Tuple, Union

import sdl2
import sdl2.ext
from sdl2 import sdlgfx, sdlttf

from sdl_gui import core, markdown
from sdl_gui.layout_engine.node import FlexNode
from sdl_gui.layout_engine.style import FlexStyle
from sdl_gui.layout_engine.definitions import FlexDirection, JustifyContent, AlignItems, FlexWrap


class RawTexture(sdl2.ext.Texture):
    """A Texture wrapper that can be initialized from an existing SDL_Texture."""
    def __init__(self, renderer: Union[sdl2.ext.Renderer, Any], tx: Any):
        # We bypass the standard __init__ since it requires a surface
        self._renderer_ref = None
        if isinstance(renderer, sdl2.ext.Renderer):
            self._renderer_ref = renderer._renderer_ref
        elif hasattr(renderer, "contents") and isinstance(renderer.contents, sdl2.SDL_Renderer):
            self._renderer_ref = [renderer]
        
        if self._renderer_ref is None:
            raise TypeError("renderer must be a valid Renderer or SDL_Renderer pointer")
            
        self._tx = tx
        # Cache size
        w, h = ctypes.c_int(), ctypes.c_int()
        sdl2.SDL_QueryTexture(tx, None, None, ctypes.byref(w), ctypes.byref(h))
        self._size = (w.value, h.value)

    def __del__(self):
        # Inherited destroy() will call SDL_DestroyTexture(self.tx)
        if hasattr(self, "_tx"):
             self.destroy()

class Renderer:
    """Handles rendering of the display list using SDL2."""

    def __init__(self, window: sdl2.ext.Window, flags: int = sdl2.SDL_RENDERER_ACCELERATED):
        self.window = window
        self.renderer = sdl2.ext.Renderer(self.window, flags=flags)

        try:
            sdlttf.TTF_Init()
            self.ttf_available = True
        except Exception as e:
            print(f"Warning: Failed to initialize SDL_ttf: {e}")
            self.ttf_available = False

        self._font_cache: Dict[str, sdl2.ext.FontManager] = {}
        self._image_cache: Dict[str, sdl2.ext.Texture] = {}
        self._text_texture_cache: Dict[Tuple, sdl2.ext.Texture] = {}
        self._measurement_cache: Dict[Tuple[str, int], int] = {}

        self._render_queue: List[sdl2.SDL_Rect] = []
        self._render_queue_color: Tuple[int, int, int, int] = None

        self._last_window_size = (0, 0)
        self._hit_list: List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]] = []

        self._last_display_list: List[Dict[str, Any]] = []
        self._display_list_lock = threading.Lock()

    def clear(self, color=(0, 0, 0, 0)):
        r, g, b, a = color
        sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, r, g, b, a)
        self.renderer.clear()
        self._hit_list = []

    def present(self):
        self.renderer.present()

    def get_hit_list(self) -> List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]]:
        return self._hit_list

    def get_last_display_list(self) -> List[Dict[str, Any]]:
        """Return a JSON-serializable copy of the last rendered display list."""
        with self._display_list_lock:
            return self._sanitize_list(self._last_display_list)

    def _sanitize_list(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self._sanitize_item(item) for item in items]

    def _sanitize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert non-serializable items to strings/serializable values."""
        sanitized = {}
        for k, v in item.items():
            if k == core.KEY_CHILDREN and isinstance(v, list):
                sanitized[k] = self._sanitize_list(v)
            elif isinstance(v, (bytes, bytearray)):
                sanitized[k] = f"<bytes: {len(v)}>"
            elif callable(v):
                sanitized[k] = f"<callable: {v.__name__ if hasattr(v, '__name__') else 'anonymous'}>"
            elif isinstance(v, (tuple, list)):
                sanitized[k] = list(v)
            elif isinstance(v, (int, float, str, bool)) or v is None:
                sanitized[k] = v
            else:
                sanitized[k] = str(v)
        return sanitized

    def save_screenshot(self, filename: str) -> None:
        w, h = self.window.size
        surface = sdl2.SDL_CreateRGBSurface(0, w, h, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
        sdl2.SDL_RenderReadPixels(self.renderer.sdlrenderer, None,
                                  sdl2.SDL_PIXELFORMAT_ARGB8888,
                                  surface.contents.pixels,
                                  surface.contents.pitch)
        sdl2.SDL_SaveBMP(surface, filename.encode('utf-8'))
        sdl2.SDL_FreeSurface(surface)

    def render_list(self, display_list: List[Dict[str, Any]]) -> None:
        width, height = self.window.size
        self.renderer.logical_size = (width, height)
        root_rect = (0, 0, width, height)

        if (width, height) != self._last_window_size:
             self._measurement_cache = {}
             self._last_window_size = (width, height)

        # Store for debug dump
        with self._display_list_lock:
            self._last_display_list = display_list

        for item in display_list:
            self._render_item(item, root_rect)

        self._flush_render_queue()
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)

    def render_item_direct(self, item: Dict[str, Any], rect: Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]) -> None:
        # Cast to int for SDL
        x, y, w, h = rect
        rect = (int(x), int(y), int(w), int(h))
        item_type = item.get(core.KEY_TYPE)
        if item_type == core.TYPE_TEXT:
            self._render_text(item, rect)
        elif item_type == core.TYPE_INPUT:
            self._render_input(item, rect)
        elif item_type == core.TYPE_RECT:
            self._draw_rect_primitive(item, rect)
        elif item_type == core.TYPE_IMAGE:
            self._flush_render_queue()
            self._render_image(item, rect)
        elif item_type == core.TYPE_FLEXBOX:
            self._render_flexbox(item, rect)
        self._flush_render_queue()

    def _render_item(self, item: Dict[str, Any], parent_rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        raw_rect = item.get(core.KEY_RECT)
        current_rect = parent_rect

        if raw_rect:
            px, py, pw, ph = parent_rect
            if raw_rect[2] == "auto": rw = self._measure_item_width(item, ph)
            else: rw = self._resolve_val(raw_rect[2], pw)

            if raw_rect[3] == "auto": rh = self._measure_item(item, rw, ph)
            else: rh = self._resolve_val(raw_rect[3], ph)

            rx = self._resolve_val(raw_rect[0], pw)
            ry = self._resolve_val(raw_rect[1], ph)
            current_rect = (px + rx, py + ry, rw, rh)

        self._hit_list.append((current_rect, item))
        item_type = item.get(core.KEY_TYPE)

        if item_type == core.TYPE_LAYER:
            for child in item.get(core.KEY_CHILDREN, []):
                self._render_item(child, current_rect, viewport)
        elif item_type == core.TYPE_SCROLLABLE_LAYER:
            self._render_scrollable_layer(item, current_rect, viewport)
        elif item_type == core.TYPE_VBOX:
            self._render_vbox(item, current_rect, viewport)
        elif item_type == core.TYPE_HBOX:
            self._render_hbox(item, current_rect, viewport)
        elif item_type == core.TYPE_RECT:
            self._draw_rect_primitive(item, current_rect, raw_rect)
        elif item_type == core.TYPE_TEXT:
            self._render_text(item, current_rect)
        elif item_type == core.TYPE_IMAGE:
            self._render_image(item, current_rect)
        elif item_type == core.TYPE_INPUT:
            self._render_input(item, current_rect)
        elif item_type == core.TYPE_FLEXBOX:
            self._render_flexbox(item, current_rect, viewport)

    def _render_flexbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        """Render a FlexBox item by building a FlexNode tree and resolving layout."""
        x, y, w, h = rect
        
        # 1. Build Flex Tree
        root_node = self._build_flex_tree(item, w, h)
        
        # 2. Calculate Layout
        import logging
        logging.debug(f"RENDER FLEXBOX: entry={x, y, w, h}")
        root_node.calculate_layout(w, h, x_offset=x, y_offset=y, force_size=True)
        
        # 3. Render Background (if color/border exists)
        if item.get(core.KEY_COLOR) or item.get(core.KEY_BORDER_COLOR):
            self._draw_rect_primitive(item, rect)
            
        # 4. Render Children using calculated positions
        self._render_flex_node_children(root_node, item, viewport)

    def _build_flex_tree(self, item: Dict[str, Any], parent_w: int, parent_h: int) -> FlexNode:
        style = FlexStyle()
        
        # Map Flex Properties
        style.direction = FlexDirection(item.get(core.KEY_FLEX_DIRECTION, "row"))
        style.justify_content = JustifyContent(item.get(core.KEY_JUSTIFY_CONTENT, JustifyContent.FLEX_START.value))
        style.align_items = AlignItems(item.get(core.KEY_ALIGN_ITEMS, AlignItems.STRETCH.value))
        style.wrap = FlexWrap(item.get(core.KEY_FLEX_WRAP, "nowrap"))
        style.gap = item.get(core.KEY_GAP, 0)
        
        # Box Model
        style.grow = item.get(core.KEY_FLEX_GROW, 0.0)
        style.shrink = item.get(core.KEY_FLEX_SHRINK, 1.0)
        style.basis = item.get(core.KEY_FLEX_BASIS, "auto")
        style.padding = self._normalize_box_model(item.get(core.KEY_PADDING, (0, 0, 0, 0)))
        style.margin = self._normalize_box_model(item.get(core.KEY_MARGIN, (0, 0, 0, 0)))
        
        # Determine Explicit Size if any
        # This is tricky because item might rely on parent logic.
        # But here we are building the node for THIS item.
        # Its w/h in style are essentially constraints or basis.
        raw_rect = item.get(core.KEY_RECT)
        if raw_rect:
            # If explicit rect is set in primitive, use it?
            # primitive rect is (x,y,w,h).
            if raw_rect[2] != "auto":
                 style.width = raw_rect[2] # String check handled by node
            if raw_rect[3] != "auto":
                 style.height = raw_rect[3]
        
        # Recursively build children
        node = FlexNode(style)
        
        # Important: Link the original item to the node for rendering later
        node.original_item = item 
        
        if item.get(core.KEY_TYPE) != core.TYPE_FLEXBOX:
            # Leaf node: provide a measure function
            # Use default arg to capture the CURRENT item in the closure!
            node.measure_func = lambda av_w, av_h, it=item: (
                self._measure_item_width(it, av_w, av_h),
                self._measure_item(it, av_w, av_h)
            )
        else:
            for child in item.get(core.KEY_CHILDREN, []):
                child_node = self._build_flex_tree(child, 0, 0)
                node.add_child(child_node)
            
        return node

    def _render_flex_node_children(self, node: FlexNode, item: Dict[str, Any], viewport: Tuple[int, int, int, int] = None):
        # We need to map node children back to item children.
        # Since we preserved order, we can iterate.
        
        # item['children'] corresponds to node.children
        # We need to render each child using the computed layout from node.
        
        for i, child_node in enumerate(node.children):
            # Retrieve original item
            if hasattr(child_node, 'original_item'):
                 child_item = child_node.original_item
            else:
                 continue
            
            # Use the computed rect
            cx, cy, cw, ch = child_node.layout_rect
            
            # Check viewport
            if viewport:
                 # Simple intersection check
                 if (cx + cw < viewport[0] or cx > viewport[0] + viewport[2] or
                     cy + ch < viewport[1] or cy > viewport[1] + viewport[3]):
                     pass # Skip? No, let's just check standard render viewport logic
                     # Actually standard render item checks strict intersection?
            
            # Recursive render
            if child_item.get(core.KEY_TYPE) == core.TYPE_FLEXBOX:
                 # If child is also flexbox, we shouldn't re-calculate layout?
                 # Wait, we already calculated the entire tree layout in root!
                 # So we should render it using the computed positions.
                 # BUT _render_flexbox calls calculate_layout again on root.
                 # If we call _render_flexbox recursively, we are re-calculating sub-tree!
                 # Ideally, we should have a `_render_flex_node_tree` method that does not re-calc.
                 self._render_flex_node_tree_pass(child_node, viewport)
            else:
                 # Regular item (Text, Image, Rect...)
                 # We treat it as a leaf?
                 # But standard primitives expect _render_item to resolve their rect?
                 # _render_item takes (parent_rect) and resolves offsets.
                 # HERE we have absolute rect for the child.
                 # So we should call a method that accepts absolute rect.
                 self.render_item_direct(child_item, (cx, cy, cw, ch))

    def _render_flex_node_tree_pass(self, node: FlexNode, viewport: Tuple[int, int, int, int]):
         # Render the node itself (background)
         item = getattr(node, 'original_item', {})
         x, y, w, h = node.layout_rect
         rect = (int(x), int(y), int(w), int(h))
         
         if item.get(core.KEY_COLOR):
             self._draw_rect_primitive(item, rect)
             
         self._render_flex_node_children(node, item, viewport)

    def _flush_render_queue(self):
        if not self._render_queue: return
        count = len(self._render_queue)
        rects_array = (sdl2.SDL_Rect * count)(*self._render_queue)
        r, g, b, a = self._render_queue_color
        sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, r, g, b, a)
        sdl2.SDL_RenderFillRects(self.renderer.sdlrenderer, rects_array, count)
        self._render_queue = []
        self._render_queue_color = None

    def _to_sdlgfx_color(self, color: Tuple[int, int, int, int]) -> int:
        r, g, b, a = color
        return (a << 24) | (b << 16) | (g << 8) | r

    def _draw_rect_primitive(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], raw_rect_check: Any = True) -> None:
        if not raw_rect_check: return
        color = item.get("color", (255, 255, 255, 255))
        if len(color) == 3: color = (*color, 255)

        radius = item.get(core.KEY_RADIUS, 0)
        x, y, w, h = rect
        if radius > 0:
            radius = min(radius, w // 2, h // 2)

        if radius > 0:
            self._flush_render_queue()
            self._draw_aa_rounded_box(rect, radius, color)
        else:
             # Skip fill if fully transparent
             if color[3] == 0:
                 pass
             elif self._render_queue_color == color:
                 self._render_queue.append(sdl2.SDL_Rect(x, y, w, h))
             else:
                 self._flush_render_queue()
                 self._render_queue_color = color
                 self._render_queue.append(sdl2.SDL_Rect(x, y, w, h))

        self._draw_border(item, rect, radius)

    def _draw_border(self, item, rect, radius):
        border_color = item.get(core.KEY_BORDER_COLOR)
        border_width = item.get(core.KEY_BORDER_WIDTH, 0)
        if border_width <= 0 or not border_color: return

        if len(border_color) == 3: border_color = (*border_color, 255)
        x, y, w, h = rect

        if radius <= 0:
            self._flush_render_queue()
            b_color = sdl2.ext.Color(*border_color)
            for i in range(border_width):
                 self.renderer.draw_rect((x+i, y+i, w-2*i, h-2*i), b_color)
        else:
            self._flush_render_queue()
            gfx_b_color = self._to_sdlgfx_color(border_color)
            for i in range(border_width):
                 bx, by = x + i, y + i
                 bw, bh = w - 2 * i, h - 2 * i
                 if bw <= 0 or bh <= 0: break
                 curr_r = max(0, radius - i)
                 if curr_r > 0:
                     sdlgfx.roundedRectangleColor(self.renderer.sdlrenderer, bx, by, bx+bw-1, by+bh-1, curr_r, gfx_b_color)
                 else:
                     self.renderer.draw_rect((bx, by, bw, bh), sdl2.ext.Color(*border_color))

    def _draw_aa_rounded_box(self, rect: Tuple[int, int, int, int], radius: int, color: Tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        gfx_color = self._to_sdlgfx_color(color)

        sdlgfx.roundedBoxColor(self.renderer.sdlrenderer, x, y, x + w - 1, y + h - 1, radius, gfx_color)
        sdlgfx.aalineColor(self.renderer.sdlrenderer, x + radius, y, x + w - 1 - radius, y, gfx_color)
        sdlgfx.aalineColor(self.renderer.sdlrenderer, x + radius, y + h - 1, x + w - 1 - radius, y + h - 1, gfx_color)
        sdlgfx.aalineColor(self.renderer.sdlrenderer, x, y + radius, x, y + h - 1 - radius, gfx_color)
        sdlgfx.aalineColor(self.renderer.sdlrenderer, x + w - 1, y + radius, x + w - 1, y + h - 1 - radius, gfx_color)

        def set_clip(cx, cy, cw, ch):
             clip = sdl2.SDL_Rect(cx, cy, cw, ch)
             sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, ctypes.byref(clip))

        set_clip(x, y, radius, radius); sdlgfx.aacircleColor(self.renderer.sdlrenderer, x + radius, y + radius, radius, gfx_color)
        set_clip(x + w - radius, y, radius, radius); sdlgfx.aacircleColor(self.renderer.sdlrenderer, x + w - 1 - radius, y + radius, radius, gfx_color)
        set_clip(x + w - radius, y + h - radius, radius, radius); sdlgfx.aacircleColor(self.renderer.sdlrenderer, x + w - 1 - radius, y + h - 1 - radius, radius, gfx_color)
        set_clip(x, y + h - radius, radius, radius); sdlgfx.aacircleColor(self.renderer.sdlrenderer, x + radius, y + h - 1 - radius, radius, gfx_color)
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)

    def _render_vbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        x, y, w, h = rect
        if item.get(core.KEY_COLOR): self._draw_rect_primitive(item, rect)

        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        pt = self._resolve_val(raw_padding[0], h)
        pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h)
        pl = self._resolve_val(raw_padding[3], w)

        cursor_y = y + pt
        av_w = w - pr - pl
        av_h = h - pt - pb

        for child in item.get(core.KEY_CHILDREN, []):
            raw_margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
            mt = self._resolve_val(raw_margin[0], av_h)
            mb = self._resolve_val(raw_margin[2], av_h)
            ml = self._resolve_val(raw_margin[3], av_w)

            cw_raw = child.get(core.KEY_RECT, [0,0,0,0])
            cw = self._resolve_val(cw_raw[2], av_w)
            ch = self._measure_item(child, cw, av_h)

            c_rect = (x + pl + ml, cursor_y + mt, cw, ch)

            if not viewport or (cursor_y + mt + ch >= viewport[1] and cursor_y + mt <= viewport[1] + viewport[3]):
                self._render_element_at(child, c_rect, viewport)

            cursor_y += mt + ch + mb

    def _render_hbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        x, y, w, h = rect
        if item.get(core.KEY_COLOR): self._draw_rect_primitive(item, rect)

        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        pt = self._resolve_val(raw_padding[0], h)
        pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h)
        pl = self._resolve_val(raw_padding[3], w)

        cursor_x = x + pl
        av_w = w - pr - pl
        av_h = h - pt - pb

        for child in item.get(core.KEY_CHILDREN, []):
            raw_margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
            mt = self._resolve_val(raw_margin[0], av_h)
            ml = self._resolve_val(raw_margin[3], av_w)
            mr = self._resolve_val(raw_margin[1], av_w)

            cw_raw = child.get(core.KEY_RECT, [0,0,0,0])
            cw = self._measure_item_width(child, av_h) if cw_raw[2] == "auto" else self._resolve_val(cw_raw[2], av_w)
            ch = self._measure_item(child, cw, av_h)

            c_rect = (cursor_x + ml, y + pt + mt, cw, ch)

            if not viewport or (cursor_x + ml + cw >= viewport[0] and cursor_x + ml <= viewport[0] + viewport[2]):
                 self._render_element_at(child, c_rect, viewport)

            cursor_x += ml + cw + mr

    def _render_element_at(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        # Same dispatcher as _render_item, but specifically for explicit rects.
        # We can reuse _render_item but need to ensure it processes the given rect.
        # Since _render_item calculates rect from parent+relative, we can pass (0,0,0,0) as parent
        # and ensure child has absolute rect? No.
        # Just manually call the specific render method.
        typ = item.get(core.KEY_TYPE)
        if typ == core.TYPE_VBOX: self._render_vbox(item, rect, viewport)
        elif typ == core.TYPE_HBOX: self._render_hbox(item, rect, viewport)
        elif typ == core.TYPE_RECT: self._draw_rect_primitive(item, rect)
        elif typ == core.TYPE_TEXT: self._render_text(item, rect)
        elif typ == core.TYPE_IMAGE:
             self._flush_render_queue()
             self._render_image(item, rect)
        elif typ == core.TYPE_INPUT:
             self._render_input(item, rect)

    def _render_scrollable_layer(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        x, y, w, h = rect
        scroll_y = item.get(core.KEY_SCROLL_Y, 0)

        clip_rect = sdl2.SDL_Rect(x, y, w, h)
        self._flush_render_queue()
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, clip_rect)

        virtual_parent_rect = (x, y - scroll_y, w, h)
        current_viewport = (x, y, w, h)

        for child in item.get(core.KEY_CHILDREN, []):
            self._render_item(child, virtual_parent_rect, current_viewport)

        self._flush_render_queue()
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)

    def _get_font_manager(self, font_path, size, color, bold=False):
        cache_key = f"{font_path}_{size}_{color}_{bold}"
        font_manager = self._font_cache.get(cache_key)
        if not font_manager:
            try:
                font_manager = sdl2.ext.FontManager(font_path, size=size, color=color)
                if bold and hasattr(font_manager, "font"):
                    sdlttf.TTF_SetFontStyle(font_manager.font, sdlttf.TTF_STYLE_BOLD)
                self._font_cache[cache_key] = font_manager
            except Exception:
                return None
        return font_manager

    def _render_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        self._flush_render_queue()
        if not self.ttf_available or not item.get(core.KEY_TEXT, ""): return

        if item.get(core.KEY_MARKUP, True):
             self._render_rich_text(item, rect)
             return

        lines, settings = self._layout_plain_text(item, rect)
        self._draw_plain_text_lines(lines, settings, rect)

    def _layout_plain_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> Tuple[List[str], Dict]:
        text = item.get(core.KEY_TEXT, "")
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        size = self._get_resolved_font_size(item, rect[3])
        color = item.get(core.KEY_COLOR, (0, 0, 0, 255))

        fm = self._get_font_manager(font_path, size, color)
        if not fm: return [], {}

        def measure(s): surf = fm.render(s); return (surf.w if surf else 0, surf.h if surf else 0)

        lines = [text] if not item.get(core.KEY_WRAP, True) else self._wrap_text(text, measure, rect[2])
        _, lh = measure("Tg")

        if len(lines) * lh > rect[3] and item.get(core.KEY_ELLIPSIS, True):
            lines = self._apply_ellipsis(lines, measure, rect[2], rect[3], lh)

        settings = {"font_path": font_path, "size": size, "color": color,
            "align": item.get(core.KEY_ALIGN, "left"), "line_h": lh, "fm": fm}
        return lines, settings

    def _wrap_text(self, text, measure_func, max_width):
        words = text.split(" ")
        lines = []; current_line = []
        for word in words:
            test = " ".join(current_line + [word])
            w, _ = measure_func(test)
            if w > max_width and current_line:
                 lines.append(" ".join(current_line)); current_line = [word]
            else: current_line.append(word)
        if current_line: lines.append(" ".join(current_line))
        return lines

    def _apply_ellipsis(self, lines, measure, max_w, max_h, line_h):
        max_l = max(1, max_h // line_h)
        if len(lines) > max_l:
            lines = lines[:max_l]; last = lines[-1]
            while True:
                w, _ = measure(last + "...")
                if w <= max_w: lines[-1] = last + "..."; break
                if not last: break
                last = last[:-1]
        return lines

    def _draw_plain_text_lines(self, lines, settings, rect):
        cy = rect[1]; max_y = rect[1] + rect[3]
        for line in lines:
            if cy > max_y: break
            cache_key = (settings["font_path"], settings["size"], tuple(settings["color"]), line)
            texture = self._text_texture_cache.get(cache_key)
            if not texture:
                s = settings["fm"].render(line)
                if not s: continue
                texture = sdl2.ext.Texture(self.renderer, s)
                self._text_texture_cache[cache_key] = texture

            tw, th = texture.size
            tx = rect[0]
            if settings["align"] == "center": tx += (rect[2] - tw) // 2
            elif settings["align"] == "right": tx += rect[2] - tw
            self.renderer.copy(texture, dstrect=(tx, cy, tw, th))
            cy += settings["line_h"]

    def _render_rich_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        lines, settings = self._layout_rich_text(item, rect)
        self._draw_rich_text_lines(lines, settings, rect, item)

    def _layout_rich_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]):
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        size = self._get_resolved_font_size(item, rect[3])
        base_color = item.get(core.KEY_COLOR, (0, 0, 0, 255))

        parser = markdown.MarkdownParser(default_color=base_color)
        segments = parser.parse(item.get(core.KEY_TEXT, ""))

        def measure_chunk(text_str, seg):
            fm = self._get_font_manager(font_path, size, seg.color, seg.bold)
            s = fm.render(text_str) if fm else None
            return (s.w, s.h) if s else (0,0)

        lines = self._wrap_rich_text(segments, measure_chunk, rect[2], item.get(core.KEY_WRAP, True))
        _, lh = measure_chunk("Tg", segments[0] if segments else None)
        line_height = lh if lh > 0 else size

        settings = {"font_path": font_path, "size": size, "line_h": line_height}
        return lines, settings

    def _get_resolved_font_size(self, item, parent_h):
        raw = item.get(core.KEY_FONT_SIZE, 16)
        s = self._resolve_val(raw, parent_h) if parent_h > 0 else (raw if isinstance(raw, int) else 16)
        return s if s > 0 else 16

    def _wrap_rich_text(self, segments, measure_func, max_width, do_wrap):
        chunked = self._tokenize_rich_text(segments)
        lines = []; current_line = []; curr_w = 0
        for txt, seg in chunked:
            if txt == "\n":
                lines.append(current_line); current_line = []; curr_w = 0; continue
            w, h = measure_func(txt, seg)
            if do_wrap and current_line and (curr_w + w > max_width):
                lines.append(current_line); current_line = [(txt, seg, w, h)]; curr_w = w
            else:
                current_line.append((txt, seg, w, h)); curr_w += w
        if current_line: lines.append(current_line)
        return lines

    def _tokenize_rich_text(self, segments):
        chunked = []
        for seg in segments:
            lines = seg.text.split('\n')
            for i, line in enumerate(lines):
                words = line.split(" ")
                for j, w in enumerate(words):
                    suf = " " if j < len(words) - 1 else ""
                    if w+suf: chunked.append((w+suf, seg))
                if i < len(lines) - 1: chunked.append(("\n", seg))
        return chunked

    def _draw_rich_text_lines(self, lines, settings, rect, item):
        curr_y = rect[1]; start_x = rect[0]; max_w = rect[2]
        align = item.get(core.KEY_ALIGN, "left")

        for line in lines:
            line_h = settings["line_h"]
            for _, _, _, h in line: line_h = max(line_h, h)

            lx = start_x
            if align == "center":
                 lw = sum([c[2] for c in line])
                 lx += (max_w - lw) // 2

            for txt, seg, w, h in line:
                self._draw_rich_chunk(txt, seg, lx, curr_y, w, h, settings)
                if seg.link_target:
                    self._hit_list.append(((lx, curr_y, w, h), {
                        "type": "link", "target": seg.link_target,
                        core.KEY_LISTEN_EVENTS: [core.EVENT_CLICK]
                    }))
                lx += w
            curr_y += line_h

    def _draw_rich_chunk(self, txt, seg, x, y, w, h, settings):
        cache_key = (settings["font_path"], settings["size"], tuple(seg.color), txt, seg.bold)
        texture = self._text_texture_cache.get(cache_key)
        if not texture:
            fm = self._get_font_manager(settings["font_path"], settings["size"], seg.color, seg.bold)
            if fm:
                surf = fm.render(txt)
                if surf:
                    texture = sdl2.ext.Texture(self.renderer, surf)
                    self._text_texture_cache[cache_key] = texture
        if texture:
            self.renderer.copy(texture, dstrect=(x, y, *texture.size))

    def _render_image(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
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

        # 3. Handle Rounded Corners
        if radius > 0:
            radius = min(radius, final_w // 2, final_h // 2)
            
        if radius > 0:
            rounded_key = f"rounded_{orig_cache_key}_{final_w}_{final_h}_{radius}"
            rounded_texture = self._image_cache.get(rounded_key)
            if not rounded_texture:
                self._flush_render_queue()
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
        
        # Draw mask (white rounded box)
        self._draw_aa_rounded_box((0, 0, w, h), radius, (255, 255, 255, 255))
        
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

        surface = None
        if isinstance(source, str): surface = img.IMG_Load(source.encode('utf-8'))
        elif isinstance(source, (bytes, bytearray)):
            rw = sdl2.rwops.rw_from_object(source)
            surface = img.IMG_Load_RW(rw, 0)
        elif callable(source):
            res = source()
            if isinstance(res, sdl2.SDL_Surface): surface = res
            elif hasattr(res, "contents") and isinstance(res.contents, sdl2.SDL_Surface): surface = res
            elif isinstance(res, (bytes, bytearray)): return self._load_image_source(res)
        return surface

    def _normalize_box_model(self, val) -> Tuple[int, int, int, int]:
        if isinstance(val, (int, float)): return (int(val), int(val), int(val), int(val))
        if isinstance(val, (list, tuple)):
            if len(val) == 1: return (int(val[0]), int(val[0]), int(val[0]), int(val[0]))
            if len(val) == 2: return (int(val[0]), int(val[1]), int(val[0]), int(val[1]))
            if len(val) == 4: return (int(val[0]), int(val[1]), int(val[2]), int(val[3]))
        return (0, 0, 0, 0)

    def _resolve_val(self, val: Union[int, str], parent_len: int) -> int:
        if isinstance(val, int): return val
        elif isinstance(val, str):
            if val.endswith("%"):
                try: pct = float(val[:-1]); return int(parent_len * (pct / 100))
                except ValueError: return 0
            elif val.endswith("px"):
                try: return int(val[:-2])
                except ValueError: return 0
            else:
                 try: return int(val)
                 except ValueError: return 0
        return 0

    def _measure_item(self, item: Dict[str, Any], available_width: int, available_height: int = 0) -> int:
        """Returns the HEIGHT of the item."""
        item_id = item.get(core.KEY_ID)
        cache_key = (item_id, available_width, "h") if item_id else None
        if cache_key and cache_key in self._measurement_cache: return self._measurement_cache[cache_key]

        if core.KEY_RECT in item:
            raw_height = item[core.KEY_RECT][3]
            if raw_height != "auto":
                 return self._resolve_val(raw_height, available_height)

        h = 0
        typ = item.get(core.KEY_TYPE)
        if typ == core.TYPE_TEXT: h = self._measure_text_height(item, available_width, available_height)
        elif typ == core.TYPE_VBOX: h = self._measure_vbox_height(item, available_width, available_height)
        elif typ == core.TYPE_IMAGE: h = self._measure_image_height(item, available_width)
        elif core.KEY_RECT in item:
             rh = item[core.KEY_RECT][3]
             if rh != "auto":
                  h = self._resolve_val(rh, available_height)
        elif typ == core.TYPE_FLEXBOX: h = self._measure_flexbox_height(item, available_width, available_height)

        if cache_key: self._measurement_cache[cache_key] = h
        return h

    def _measure_item_width(self, item: Dict[str, Any], available_width: int, available_height: int = 0) -> int:
        """Returns the WIDTH of the item."""
        item_id = item.get(core.KEY_ID)
        cache_key = (item_id, available_width, "w") if item_id else None
        if cache_key and cache_key in self._measurement_cache: return self._measurement_cache[cache_key]

        if core.KEY_RECT in item:
            raw_width = item[core.KEY_RECT][2]
            if raw_width != "auto":
                 return self._resolve_val(raw_width, available_width)

        w = 0
        typ = item.get(core.KEY_TYPE)
        if typ == core.TYPE_TEXT: w = self._measure_text_width(item, available_height)
        elif typ == core.TYPE_FLEXBOX: w = self._measure_flexbox_width(item, available_width, available_height)
        elif core.KEY_RECT in item:
             # If primitive has a fixed rect, use its width
             rw = item[core.KEY_RECT][2]
             if rw != "auto":
                  w = self._resolve_val(rw, available_width)
        elif typ == core.TYPE_IMAGE:
             src = item.get(core.KEY_SOURCE)
             if src:
                 s = self._load_image_source(src)
                 w = s.w if s else 0
        
        if cache_key: self._measurement_cache[cache_key] = w
        return w

    def _measure_vbox_height(self, item: Dict[str, Any], av_w: int, av_h: int) -> int:
        pad = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        h_sum = self._resolve_val(pad[0], av_h) + self._resolve_val(pad[2], av_h)
        iw = max(0, av_w - self._resolve_val(pad[3], av_w) - self._resolve_val(pad[1], av_w))
        ih = max(0, av_h - h_sum)

        for child in item.get(core.KEY_CHILDREN, []):
            m = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
            mt = self._resolve_val(m[0], ih); mb = self._resolve_val(m[2], ih)
            cw_raw = child.get(core.KEY_RECT, [0,0,100,0])[2]
            cw = self._resolve_val(cw_raw, iw)
            h_sum += mt + self._measure_item(child, cw, ih) + mb
        return h_sum

    def _measure_flexbox_height(self, item: Dict[str, Any], av_w: int, av_h: int) -> int:
        # To measure, we effectively run the layout with 'auto' height on root?
        # Or we rely on the engine to tell us the content height.
        # But our engines `calculate_layout` calculates positions given a size.
        # It doesn't inherently "shrink wrap" unless specified.
        
        # However, if we pass av_h=0 or 'auto', the engine might struggle if not designed for it.
        # BUT, FlexNode logic:
        # If height is None/Auto, it tries to grow/shrink or fit content.
        # We need a mode in FlexNode to "measure content".
        
        # Strategy:
        # 1. Build tree.
        # 2. Force root height to be 'auto' or 0 (if av_h is constrained).
        # 3. Calculate layout.
        # 4. Check the resulting height of the root node.
        
        # Note: We must NOT pass force_size=True here, because we want natural size.
        
        node = self._build_flex_tree(item, av_w, av_h)
        # Hack: ensure style.height is None so it calculates naturally if it was "auto"
        # _build_flex_tree maps "auto" to None (via `if raw_rect[3] != "auto": style.height = ...`). 
        # So it should be fine.
        
        # We run layout with available width. 
        # If av_h is 0, we treat it as infinite for measurement? Or 0?
        # Usually measurement means "how much space do you NEED".
        # So we give it available width, and infinite height?
        available_h_for_calc = av_h if av_h > 0 else 99999
        
        try:
             node.calculate_layout(av_w, available_h_for_calc, force_size=False)
             return int(node.layout_rect[3])
        except Exception:
             return 0

    def _measure_hbox_height(self, item: Dict[str, Any], av_w: int, av_h: int) -> int:
        pad = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        pt = self._resolve_val(pad[0], av_h); pb = self._resolve_val(pad[2], av_h)
        iw = max(0, av_w - self._resolve_val(pad[3], av_w) - self._resolve_val(pad[1], av_w))
        ih = max(0, av_h - pt - pb)
        max_h = 0

        for child in item.get(core.KEY_CHILDREN, []):
            m = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
            mt = self._resolve_val(m[0], ih); mb = self._resolve_val(m[2], ih)
            cw_raw = child.get(core.KEY_RECT, [0,0,100,0])[2]
            cw = self._resolve_val(cw_raw, iw)
            max_h = max(max_h, mt + self._measure_item(child, cw, ih) + mb)
        return pt + max_h + pb

    def _measure_flexbox_width(self, item: Dict[str, Any], av_w: int, av_h: int) -> int:
        node = self._build_flex_tree(item, av_w, av_h)
        available_h_for_calc = av_h if av_h > 0 else 99999
        try:
             node.calculate_layout(av_w, available_h_for_calc, force_size=False)
             return int(node.layout_rect[2])
        except Exception:
             return 0

    def _measure_hbox_width(self, item: Dict[str, Any], parent_height: int) -> int:
        pad = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        w_sum = self._resolve_val(pad[3], 0) + self._resolve_val(pad[1], 0)
        children = item.get(core.KEY_CHILDREN, [])
        for child in children:
            m = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
            w_sum += self._resolve_val(m[3], 0) + self._resolve_val(m[1], 0)
            cw_raw = child.get(core.KEY_RECT, [0,0,"auto",0])[2]
            cw = self._measure_item_width(child, parent_height) if cw_raw == "auto" else self._resolve_val(cw_raw, 0)
            w_sum += cw
        return w_sum

    def _measure_text_width(self, item: Dict[str, Any], parent_height: int = 0) -> int:
        text = item.get(core.KEY_TEXT, "")
        if not text: return 0

        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        size = self._get_resolved_font_size(item, parent_height)
        color = item.get(core.KEY_COLOR, (0, 0, 0, 255))

        if item.get(core.KEY_MARKUP, True):
             parser = markdown.MarkdownParser(default_color=color)
             segments = parser.parse(text)
             total_w = 0
             for seg in segments:
                 fm = self._get_font_manager(font_path, size, seg.color, seg.bold)
                 if fm: s = fm.render(seg.text); total_w += s.w if s else 0
             return total_w
        else:
             fm = self._get_font_manager(font_path, size, color)
             if fm: s = fm.render(text); return s.w if s else 0
        return 0

    def _measure_text_height(self, item: Dict[str, Any], width: int, parent_height: int = 0) -> int:
        if item.get(core.KEY_MARKUP, True): return self._measure_rich_text_height(item, width, parent_height)
        else: return 20

    def _measure_rich_text_height(self, item: Dict[str, Any], width: int, parent_height: int) -> int:
        text = item.get(core.KEY_TEXT, "")
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        size = self._get_resolved_font_size(item, parent_height)

        parser = markdown.MarkdownParser(default_color=item.get(core.KEY_COLOR, (0,0,0,255)))
        segments = parser.parse(text)

        def measure_chunk(t, s):
            fm = self._get_font_manager(font_path, size, s.color, s.bold)
            s = fm.render(t) if fm else None
            return (s.w, s.h) if s else (0,0)

        lines = self._wrap_rich_text(segments, measure_chunk, width, True)
        _, lh = measure_chunk("Tg", segments[0] if segments else None)
        line_height = lh if lh > 0 else size
        return len(lines) * line_height

    def _measure_image_height(self, item: Dict[str, Any], width: int) -> int:
        source = item.get(core.KEY_SOURCE)
        if not source: return 0

        item_id = item.get(core.KEY_ID)
        cache_key = item_id if item_id else str(id(source))

        texture = self._image_cache.get(cache_key)
        if not texture:
             surface = self._load_image_source(source)
             if surface:
                 texture = sdl2.ext.Texture(self.renderer, surface)
                 sdl2.SDL_FreeSurface(surface)
                 self._image_cache[cache_key] = texture

        if not texture or texture.size[0] == 0: return 0
        return int(texture.size[1] * (width / texture.size[0]))

    def measure_text_width(self, text: str, font_path: str = None, font_size: int = 16) -> int:
        """Public helper to measure text width for a given configuration."""
        if not text: return 0
        font_path = font_path or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        fm = self._get_font_manager(font_path, font_size, (0,0,0,0)) # color doesn't matter for size
        if fm:
             s = fm.render(text)
             return s.w if s else 0
        return 0

    def _render_input(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        self._flush_render_queue()
        x, y, w, h = rect

        # 1. Draw Background & Border
        rect_item = item.copy()
        bg_color = item.get("background_color")
        if not bg_color: bg_color = (0,0,0,0)
        rect_item[core.KEY_COLOR] = bg_color

        radius = rect_item.get(core.KEY_RADIUS, 0)
        if radius > 0:
             self._draw_rect_primitive(rect_item, rect)
        else:
             if len(bg_color) == 4 and bg_color[3] > 0:
                 ix, iy, iw, ih = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
                 fill_color = sdl2.ext.Color(*bg_color)
                 self.renderer.fill((ix, iy, iw, ih), fill_color)

             self._draw_border(rect_item, rect, radius)

        # 2. Content Area
        raw_pad = item.get(core.KEY_PADDING, (5, 5, 5, 5))
        pt = self._resolve_val(raw_pad[0], h)
        pl = self._resolve_val(raw_pad[3], w)
        pr = self._resolve_val(raw_pad[1], w)
        pb = self._resolve_val(raw_pad[2], h)

        content_x = x + pl
        content_y = y + pt
        content_w = max(0, w - pl - pr)
        content_h = max(0, h - pt - pb)

        # Clipping
        self._flush_render_queue()
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, sdl2.SDL_Rect(content_x, content_y, content_w, content_h))

        text = item.get(core.KEY_TEXT, "")
        placeholder = item.get("placeholder", "")
        # ... (unchanged parts implied, need large chunk) ...
        # Can I use multiple chunks? Yes.

        # Chunk 2: Cursor Logic

        text = item.get(core.KEY_TEXT, "")
        placeholder = item.get("placeholder", "")
        cursor_pos = item.get("cursor_pos", 0)
        focused = item.get("focused", False)
        selection_start = item.get("selection_start")

        scroll_x = item.get("scroll_x", 0)
        scroll_y = item.get("scroll_y", 0)
        multiline = item.get("multiline", False)

        font_path = item.get(core.KEY_FONT)
        size = item.get(core.KEY_FONT_SIZE, 16)
        color = item.get(core.KEY_COLOR, (0,0,0,255))

        # Adjust start position by scroll
        draw_x = content_x - scroll_x
        draw_y = content_y - scroll_y

        display_text = text if text else placeholder
        display_color = color if text else (150, 150, 150, 255)

        if not text and not focused:
             if multiline:
                 # Multiline Placeholder
                 lines = placeholder.split('\n')
                 curr_ly = draw_y
                 line_h = size + 4
                 for line in lines:
                      self._render_simple_text(line, draw_x, curr_ly, font_path, size, display_color)
                      curr_ly += line_h
             else:
                 self._render_simple_text(display_text, draw_x, draw_y, font_path, size, display_color)

             self._flush_render_queue()
             sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)
             return

        # Render Text & Cursor
        if multiline:
            # Simple Multiline Rendering
            # We split by \n and draw lines.
            # Cursor positioning in multiline is complex for rendering (finding x,y of index).
            # For this iteration, we iterate to find cursor line/col.

            lines = text.split('\n')

            # Find Cursor Line/Col
            curr_idx = 0
            cursor_line_idx = 0
            cursor_col_idx = 0
            found_cursor = False

            for i, line in enumerate(lines):
                line_len = len(line) + 1 # +1 for newline char
                if not found_cursor:
                    if curr_idx + line_len > cursor_pos:
                         cursor_line_idx = i
                         cursor_col_idx = cursor_pos - curr_idx
                         found_cursor = True
                    elif curr_idx + line_len == cursor_pos and i == len(lines)-1:
                         # End of last line
                         cursor_line_idx = i
                         cursor_col_idx = len(line)
                         found_cursor = True
                curr_idx += line_len

            # Draw Lines & Selection
            line_h = size + 4
            curr_ly = draw_y

            # Global index tracker
            curr_char_idx = 0

            for i, line in enumerate(lines):
                line_len = len(line)
                line_end_idx = curr_char_idx + line_len # exclusive of newline

                # Render Selection for this line (Background)
                if focused and selection_start is not None:
                     sel_min = min(cursor_pos, selection_start)
                     sel_max = max(cursor_pos, selection_start)

                     l_start = max(sel_min, curr_char_idx)
                     l_end = min(sel_max, line_end_idx + 1)

                     if l_start < l_end:
                         rel_start = l_start - curr_char_idx
                         rel_end = l_end - curr_char_idx

                         measure_end = min(rel_end, len(line))

                         px_start = self.measure_text_width(line[:rel_start], font_path, size)
                         px_end = self.measure_text_width(line[:measure_end], font_path, size)

                         sel_w = px_end - px_start
                         if rel_end > len(line):
                             sel_w += 10

                         sel_rect = sdl2.SDL_Rect(draw_x + px_start, curr_ly, sel_w, size + 4)
                         sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, 50, 150, 255, 128)
                         sdl2.SDL_RenderFillRect(self.renderer.sdlrenderer, ctypes.byref(sel_rect))

                # Render Text (Foreground)
                self._render_simple_text(line, draw_x, curr_ly, font_path, size, display_color)

                # Cursor (if on this line)
                if focused and i == cursor_line_idx:
                    # Blink Logic
                    if item.get("cursor_visible", True):
                        cx = draw_x + self.measure_text_width(line[:cursor_col_idx], font_path, size)
                        sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, *color)
                        sdl2.SDL_RenderDrawLine(self.renderer.sdlrenderer, cx, curr_ly, cx, curr_ly + size + 2)

                curr_ly += line_h
                curr_char_idx += line_len + 1 # +1 for newline

        else:
            # Single Line with Scroll

            # Selection (Background)
            if focused and selection_start is not None:
                 start = min(cursor_pos, selection_start)
                 end = max(cursor_pos, selection_start)

                 prefix_w = self.measure_text_width(text[:start], font_path, size)
                 sel_w = self.measure_text_width(text[start:end], font_path, size)

                 sel_rect = sdl2.SDL_Rect(draw_x + prefix_w, draw_y, sel_w, size + 4)
                 sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, 50, 150, 255, 128)
                 sdl2.SDL_RenderFillRect(self.renderer.sdlrenderer, ctypes.byref(sel_rect))

            # Text (Foreground)
            self._render_simple_text(text, draw_x, draw_y, font_path, size, display_color)

            # Cursor
            if focused:
                 # Blink Logic
                 if item.get("cursor_visible", True):
                     cursor_offset = self.measure_text_width(text[:cursor_pos], font_path, size)
                     cursor_x = draw_x + cursor_offset
                     sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, *color)
                     sdl2.SDL_RenderDrawLine(self.renderer.sdlrenderer, cursor_x, draw_y, cursor_x, draw_y + size + 2)

        # Clear Clip
        self._flush_render_queue()
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)

    def _render_simple_text(self, text, x, y, font, size, color):
        if not text: return
        fm = self._get_font_manager(font or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size, color)
        if fm:
             s = fm.render(text)
             if s:
                 tex = sdl2.ext.Texture(self.renderer, s)
                 self.renderer.copy(tex, dstrect=(x, y, *tex.size))
