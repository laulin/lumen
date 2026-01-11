
import ctypes
import threading
from typing import Any, Dict, List, Tuple, Union

import sdl2
import sdl2.ext

from sdl_gui import core, utils
from sdl_gui.rendering.flex_renderer import FlexRenderer
from sdl_gui.rendering.image_renderer import ImageRenderer
from sdl_gui.rendering.input_renderer import InputRenderer
from sdl_gui.rendering.primitive_renderer import PrimitiveRenderer
from sdl_gui.rendering.text_renderer import TextRenderer
from sdl_gui.rendering.vector_renderer import VectorRenderer
from sdl_gui.window.spatial_index import SpatialIndex


class Renderer:
    """
    Handles rendering of the display list using SDL2.
    Delegates specific rendering tasks to sub-renderers.
    """

    def __init__(self, window: sdl2.ext.Window, flags: int = sdl2.SDL_RENDERER_ACCELERATED):
        self.window = window
        # Create SDL renderer
        try:
             self.renderer = sdl2.ext.Renderer(window, flags=flags)
        except Exception:
             # Fallback
             self.renderer = sdl2.ext.Renderer(window, flags=sdl2.SDL_RENDERER_SOFTWARE)

        self.renderer.blendmode = sdl2.SDL_BLENDMODE_BLEND

        # Sub-renderers
        self.primitive_renderer = PrimitiveRenderer(self.renderer)
        self.text_renderer = TextRenderer(self.renderer, self.primitive_renderer)
        self.image_renderer = ImageRenderer(self.renderer, self.primitive_renderer)
        self.vector_renderer = VectorRenderer(self.renderer, self.primitive_renderer)
        self.flex_renderer = FlexRenderer(self, self.primitive_renderer) # Pass self as proxy
        self.input_renderer = InputRenderer(self.primitive_renderer, self.text_renderer)

        # State
        self._incremental_mode = False
        self._force_full_render = True
        self._last_window_size = window.size
        self._display_list_lock = threading.RLock()
        self._last_display_list: List[Dict[str, Any]] = []
        self._prev_display_list: List[Dict[str, Any]] = []
        self._hit_list: List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]] = []

        # Caches managed by Renderer (Layout & Indexing)
        self._layout_cache: Dict[Tuple, Any] = {}
        self._item_hash_cache: Dict[str, int] = {}
        self._spatial_index = SpatialIndex()
        self._display_list_hash = 0

        # Stats
        self._culling_stats = {"rendered": 0, "skipped": 0}
        self._dirty_stats = {"full_renders": 0, "partial_renders": 0, "skipped_frames": 0}
        self._layout_cache_stats = {"hits": 0, "misses": 0}
        self._perf_stats = {}
        self._perf_timers = {}
        self._batch_stats = {"batched_rects": 0, "saved_calls": 0}
        self._draw_call_count = 0
        self._perf_enabled = False

        self.clean_caches()

    def clean_caches(self):
        """Clear all caches."""
        self._layout_cache = {}
        self._item_hash_cache = {}
        self.text_renderer.clear_caches()
        self.image_renderer.clear_cache()
        self.vector_renderer.clear_cache()
        self.flex_renderer.clear_cache()
        self._spatial_index.clear()

    def clear(self, color=(0, 0, 0, 0), partial: bool = False) -> None:
        """Clear the render target."""
        if not partial or self._force_full_render:
            self.renderer.color = color
            # Use PrimitiveRenderer flush before clear? Usually clean state.
            self.primitive_renderer.flush()
            self.renderer.clear()
        # Partial clear handles by dirty regions in render_list

    def present(self) -> None:
        self.primitive_renderer.flush()
        self.renderer.present()

    def get_hit_list(self) -> List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]]:
        return self._hit_list

    def get_last_display_list(self) -> List[Dict[str, Any]]:
        with self._display_list_lock:
            return self._sanitize_list(self._last_display_list)

    def get_culling_stats(self) -> Dict[str, int]:
        return self._culling_stats.copy()

    def get_dirty_stats(self) -> Dict[str, int]:
        return self._dirty_stats.copy()

    def set_incremental_mode(self, enabled: bool) -> None:
        self._incremental_mode = enabled
        if not enabled:
            self._force_full_render = True

    def mark_dirty(self, rect: Tuple[int, int, int, int] = None) -> None:
        # Simplified: always force full render for now or track dirty regions
        if rect is None:
            self._force_full_render = True
        else:
            self._force_full_render = True # TODO: Efficient dirty rects

    def get_layout_cache_stats(self) -> Dict[str, int]:
        return self._layout_cache_stats.copy()

    def enable_profiling(self, enabled: bool) -> None:
        self._perf_enabled = enabled
        if enabled:
            self._perf_stats = {}
            self._draw_call_count = 0
            self._batch_stats = {"batched_rects": 0, "saved_calls": 0}

    def get_perf_stats(self) -> Dict[str, Any]:
        return {
            "timings": self._perf_stats.copy(),
            "draw_calls": self._draw_call_count,
            "batch_stats": self._batch_stats.copy(),
            "culling_stats": self._culling_stats.copy(),
            "layout_cache_stats": self._layout_cache_stats.copy(),
            "spatial_index_stats": self._spatial_index.get_stats(),
        }

    def get_spatial_stats(self) -> Dict[str, int]:
        return self._spatial_index.get_stats()

    def _perf_start(self, name: str) -> None:
        if self._perf_enabled:
            import time
            self._perf_timers[name] = time.perf_counter()

    def _perf_end(self, name: str) -> None:
        if self._perf_enabled and name in self._perf_timers:
            import time
            elapsed = time.perf_counter() - self._perf_timers[name]
            self._perf_stats[name] = self._perf_stats.get(name, 0) + elapsed
            del self._perf_timers[name]

    def _get_layout_cache_key(self, item: Dict[str, Any], parent_rect: Tuple[int, int, int, int]) -> Tuple:
        children_hash = tuple(self._hash_item_cached(c) for c in item.get(core.KEY_CHILDREN, []))
        return (self._hash_item_cached(item), parent_rect, children_hash)

    def _make_hashable(self, value: Any) -> Any:
        # Re-implemented locally or use helper? It's specific to dict structure.
        if isinstance(value, dict):
            return tuple(sorted((k, self._make_hashable(v)) for k, v in value.items()))
        elif isinstance(value, list):
            return tuple(self._make_hashable(v) for v in value)
        elif isinstance(value, tuple):
            return tuple(self._make_hashable(v) for v in value)
        elif callable(value):
            return id(value)
        else:
            try:
                hash(value)
                return value
            except TypeError:
                return str(value)

    def _hash_item(self, item: Dict[str, Any]) -> int:
        hashable_parts = []
        for key, value in sorted(item.items()):
            if key == core.KEY_CHILDREN:
                continue
            hashable_parts.append((key, self._make_hashable(value)))
        return hash(tuple(hashable_parts))

    def _compute_structural_hash(self, display_list: List[Dict[str, Any]]) -> int:
        def hash_structure(items: List[Dict[str, Any]]) -> Tuple:
            result = []
            for item in items:
                item_id = item.get(core.KEY_ID, "")
                item_type = item.get(core.KEY_TYPE, "")
                rect = item.get(core.KEY_RECT)
                rect_key = tuple(rect) if rect else None
                children = item.get(core.KEY_CHILDREN, [])
                children_hash = hash_structure(children) if children else ()
                result.append((item_id, item_type, rect_key, children_hash))
            return tuple(result)
        return hash(hash_structure(display_list))

    def _hash_item_cached(self, item: Dict[str, Any]) -> int:
        item_id = item.get(core.KEY_ID)
        if item_id and item_id in self._item_hash_cache:
            return self._item_hash_cache[item_id]

        result = self._hash_item(item)
        if item_id:
            self._item_hash_cache[item_id] = result
        return result

    def _invalidate_hash_cache(self) -> None:
        self._item_hash_cache.clear()

    # Dirty region logic removed for brevity but could be reinstated from original if vital for performance.
    # For refactoring simplicity, we assume full render or simplified dirty check.
    # But `render_list` relies on it. I will keep a simplified version or reuse original logic if space permits.
    # The user complained about file size. I should remove complex dirty logic if not strictly necessary or move it?
    # I'll keep `_compute_dirty_regions` logic as it was a key performance feature.

    def _compute_dirty_regions(self, new_list: List[Dict[str, Any]], old_list: List[Dict[str, Any]], parent_rect: Tuple[int, int, int, int]) -> List[Tuple[int, int, int, int]]:
        # ... (Identical to original) ...
        dirty = []
        px, py, pw, ph = parent_rect
        if len(new_list) != len(old_list): return [parent_rect]

        for new_item, old_item in zip(new_list, old_list):
            new_rect = new_item.get(core.KEY_RECT, [0, 0, pw, ph])
            old_rect = old_item.get(core.KEY_RECT, [0, 0, pw, ph])

            # Resolve Coords
            new_x = px + self._resolve_val(new_rect[0], pw)
            new_y = py + self._resolve_val(new_rect[1], ph)
            new_w = pw if new_rect[2] == "auto" else self._resolve_val(new_rect[2], pw)
            new_h = ph if new_rect[3] == "auto" else self._resolve_val(new_rect[3], ph)

            old_x = px + self._resolve_val(old_rect[0], pw)
            old_y = py + self._resolve_val(old_rect[1], ph)
            old_w = pw if old_rect[2] == "auto" else self._resolve_val(old_rect[2], pw)
            old_h = ph if old_rect[3] == "auto" else self._resolve_val(old_rect[3], ph)

            new_abs = (new_x, new_y, new_w, new_h)
            old_abs = (old_x, old_y, old_w, old_h)

            if self._hash_item_cached(new_item) != self._hash_item_cached(old_item):
                dirty.append(old_abs)
                if old_abs != new_abs: dirty.append(new_abs)
            elif new_abs != old_abs:
                dirty.append(old_abs); dirty.append(new_abs)

            new_children = new_item.get(core.KEY_CHILDREN, [])
            old_children = old_item.get(core.KEY_CHILDREN, [])
            if new_children or old_children:
                dirty.extend(self._compute_dirty_regions(new_children, old_children, new_abs))
        return dirty

    def _merge_dirty_regions(self, regions: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        if not regions: return []
        if len(regions) == 1: return regions
        min_x = min(r[0] for r in regions)
        min_y = min(r[1] for r in regions)
        max_x = max(r[0] + r[2] for r in regions)
        max_y = max(r[1] + r[3] for r in regions)
        merged_area = (max_x - min_x) * (max_y - min_y)
        total_individual_area = sum(r[2] * r[3] for r in regions)
        if merged_area <= total_individual_area * 2:
            return [(min_x, min_y, max_x - min_x, max_y - min_y)]
        seen = set(); unique = []
        for r in regions:
            if r not in seen: seen.add(r); unique.append(r)
        return unique

    def _is_visible(self, rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> bool:
        if viewport is None: return True
        x, y, w, h = rect
        vx, vy, vw, vh = viewport
        return not (x + w <= vx or x >= vx + vw or y + h <= vy or y >= vy + vh)

    def _sanitize_list(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self._sanitize_item(item) for item in items]

    def _sanitize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for k, v in item.items():
            if k == core.KEY_CHILDREN and isinstance(v, list): sanitized[k] = self._sanitize_list(v)
            elif isinstance(v, (bytes, bytearray)): sanitized[k] = f"<bytes: {len(v)}>"
            elif callable(v): sanitized[k] = f"<callable: {v.__name__ if hasattr(v, '__name__') else 'anonymous'}>"
            elif isinstance(v, (tuple, list)): sanitized[k] = list(v)
            elif isinstance(v, (int, float, str, bool)) or v is None: sanitized[k] = v
            else: sanitized[k] = str(v)
        return sanitized

    def save_screenshot(self, filename: str) -> None:
        w, h = self.window.size
        surface = sdl2.SDL_CreateRGBSurface(0, w, h, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
        sdl2.SDL_RenderReadPixels(self.renderer.sdlrenderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, surface.contents.pixels, surface.contents.pitch)
        sdl2.SDL_SaveBMP(surface, filename.encode('utf-8'))
        sdl2.SDL_FreeSurface(surface)

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int, int]:
         rect = sdl2.SDL_Rect(x, y, 1, 1)
         pixels = ctypes.create_string_buffer(4)
         sdl2.SDL_RenderReadPixels(self.renderer.sdlrenderer, rect, sdl2.SDL_PIXELFORMAT_ABGR8888, pixels, 4)
         return (pixels.raw[0], pixels.raw[1], pixels.raw[2], pixels.raw[3])

    def render_list(self, display_list: List[Dict[str, Any]], force_full: bool = False) -> None:
        self._perf_start("render_list_total")
        width, height = self.window.size
        self.renderer.logical_size = (width, height)
        root_rect = (0, 0, width, height)
        root_viewport = root_rect

        if (width, height) != self._last_window_size:
             self.clean_caches() # Includes invalidate hash cache
             self._last_window_size = (width, height)
             self._force_full_render = True

        self._culling_stats = {"rendered": 0, "skipped": 0}
        do_full_render = force_full or self._force_full_render or not self._incremental_mode
        self._dirty_regions = []

        if not do_full_render:
            self._dirty_regions = self._compute_dirty_regions(display_list, self._prev_display_list, root_rect)
            self._dirty_regions = self._merge_dirty_regions(self._dirty_regions)
            if not self._dirty_regions:
                self._dirty_stats["skipped_frames"] += 1
                self._perf_end("render_list_total")
                return
            self._dirty_stats["partial_renders"] += 1
            if len(self._dirty_regions) == 1:
                dr = self._dirty_regions[0]
                clip_rect = sdl2.SDL_Rect(int(dr[0]), int(dr[1]), int(dr[2]), int(dr[3]))
                sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, clip_rect)
                r,g,b,a = 0,0,0,0
                sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, r, g, b, a)
                sdl2.SDL_RenderFillRect(self.renderer.sdlrenderer, clip_rect)
        else:
             self._dirty_stats["full_renders"] += 1
             self._dirty_regions = [root_rect]
             self._force_full_render = False

        self._hit_list = []
        with self._display_list_lock:
            self._last_display_list = display_list

        # Spatial Index (Simplified: always rebuild if changed)
        current_display_hash = self._compute_structural_hash(display_list)
        if current_display_hash != self._display_list_hash:
            self._display_list_hash = current_display_hash
            self._spatial_index.clear()
            self._build_spatial_index(display_list, root_rect)

        self._prev_display_list = display_list

        self._perf_start("render_items")
        for item in display_list:
            self._render_item(item, root_rect, root_viewport)
        self._perf_end("render_items")

        self.primitive_renderer.flush()
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)
        self._perf_end("render_list_total")

    def _build_spatial_index(self, items: List[Dict[str, Any]], parent_rect: Tuple[int, int, int, int], prefix: str = "") -> None:
        px, py, pw, ph = parent_rect
        for idx, item in enumerate(items):
            item_id = f"{prefix}{idx}"
            raw_rect = item.get(core.KEY_RECT)
            if raw_rect:
                rw = self._measure_item_width(item, ph) if raw_rect[2] == "auto" else self._resolve_val(raw_rect[2], pw)
                rh = self._measure_item(item, rw, ph) if raw_rect[3] == "auto" else self._resolve_val(raw_rect[3], ph)
                rx = self._resolve_val(raw_rect[0], pw)
                ry = self._resolve_val(raw_rect[1], ph)
                current_rect = (px + rx, py + ry, rw, rh)
            else:
                current_rect = parent_rect

            self._spatial_index.insert(item_id, current_rect)
            children = item.get(core.KEY_CHILDREN, [])
            if children:
                # For auto-height containers, use parent's height for children to avoid inflation
                typ = item.get(core.KEY_TYPE)
                if typ in (core.TYPE_VBOX, core.TYPE_HBOX) and raw_rect and raw_rect[3] == "auto":
                    child_rect = (current_rect[0], current_rect[1], current_rect[2], ph)
                else:
                    child_rect = current_rect
                self._build_spatial_index(children, child_rect, f"{item_id}_")

    def render_item_direct(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        rect = (int(x), int(y), int(w), int(h))
        item_type = item.get(core.KEY_TYPE)

        if item_type == core.TYPE_TEXT:
            self.text_renderer.render_text(item, rect, self._hit_list)
        elif item_type == core.TYPE_INPUT:
            self.input_renderer.render_input(item, rect)
        elif item_type == core.TYPE_RECT:
            self.primitive_renderer.draw_rect_primitive(item, rect)
        elif item_type == core.TYPE_IMAGE:
            self.image_renderer.render_image(item, rect)
        elif item_type == core.TYPE_FLEXBOX:
            self.flex_renderer.render_flexbox(item, rect) # Recursive via callback/proxy
        elif item_type == core.TYPE_VECTOR_GRAPHICS:
            self.vector_renderer.render_vector_graphics(item, rect)

        self.primitive_renderer.flush()

    def _render_item(self, item: Dict[str, Any], parent_rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        raw_rect = item.get(core.KEY_RECT)
        current_rect = parent_rect
        if raw_rect:
            px, py, pw, ph = parent_rect
            rw = self._measure_item_width(item, ph) if raw_rect[2] == "auto" else self._resolve_val(raw_rect[2], pw)
            rh = self._measure_item(item, rw, ph) if raw_rect[3] == "auto" else self._resolve_val(raw_rect[3], ph)
            rx = self._resolve_val(raw_rect[0], pw)
            ry = self._resolve_val(raw_rect[1], ph)
            current_rect = (px + rx, py + ry, rw, rh)

        if not self._is_visible(current_rect, viewport):
            self._culling_stats["skipped"] += 1
            return

        self._culling_stats["rendered"] += 1
        self._hit_list.append((current_rect, item))
        item_type = item.get(core.KEY_TYPE)

        if item_type == core.TYPE_LAYER:
            for child in item.get(core.KEY_CHILDREN, []): self._render_item(child, current_rect, viewport)
        elif item_type == core.TYPE_SCROLLABLE_LAYER:
            self._render_scrollable_layer(item, current_rect, viewport)
        elif item_type == core.TYPE_VBOX:
            self._render_vbox(item, current_rect, viewport)
        elif item_type == core.TYPE_HBOX:
            self._render_hbox(item, current_rect, viewport)
        # Delegate primitives and others
        elif item_type in [core.TYPE_RECT, core.TYPE_TEXT, core.TYPE_IMAGE, core.TYPE_INPUT, core.TYPE_FLEXBOX, core.TYPE_VECTOR_GRAPHICS]:
             self.render_item_direct(item, current_rect)

    # Legacy Layout Containers (VBox/HBox) kept in Renderer as orchestrators of their children

    def _render_vbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        x, y, w, h = rect
        if item.get(core.KEY_COLOR): self.primitive_renderer.draw_rect_primitive(item, rect)

        # Layout Caching Logic (Kept here as it's layout orchestration)
        cache_key = self._get_layout_cache_key(item, rect)
        cached_layout = self._layout_cache.get(cache_key)
        if cached_layout:
             self._layout_cache_stats["hits"] += 1
             for c_rect, child in cached_layout:
                 # Standard checks
                 if viewport and c_rect[1] > viewport[1] + viewport[3]: break
                 if viewport and c_rect[1] + c_rect[3] < viewport[1]: continue
                 self._render_element_at(child, c_rect, viewport)
             return

        self._layout_cache_stats["misses"] += 1
        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        pt = self._resolve_val(raw_padding[0], h); pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h); pl = self._resolve_val(raw_padding[3], w)

        cursor_y = y + pt
        av_w = w - pr - pl; av_h = h - pt - pb

        # First pass: compute layout for ALL children (for correct cache)
        layout_results = []
        for child in item.get(core.KEY_CHILDREN, []):
            raw_margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
            mt = self._resolve_val(raw_margin[0], av_h)
            mb = self._resolve_val(raw_margin[2], av_h)
            ml = self._resolve_val(raw_margin[3], av_w)

            cw_raw = child.get(core.KEY_RECT, [0,0,0,0])
            cw = self._resolve_val(cw_raw[2], av_w)
            ch = self._measure_item(child, cw, av_h)

            c_rect = (x + pl + ml, cursor_y + mt, cw, ch)
            layout_results.append((c_rect, child))
            cursor_y += mt + ch + mb

        # Cache the complete layout
        self._layout_cache[cache_key] = layout_results

        # Second pass: render only visible children
        for c_rect, child in layout_results:
            if viewport and c_rect[1] > viewport[1] + viewport[3]: break
            if viewport and c_rect[1] + c_rect[3] < viewport[1]: continue
            self._render_element_at(child, c_rect, viewport)

    def _render_hbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        # Similar simplification
        x, y, w, h = rect
        if item.get(core.KEY_COLOR): self.primitive_renderer.draw_rect_primitive(item, rect)

        cache_key = self._get_layout_cache_key(item, rect)
        cached_layout = self._layout_cache.get(cache_key)
        if cached_layout:
             self._layout_cache_stats["hits"] += 1
             for c_rect, child in cached_layout:
                 if viewport and c_rect[0] > viewport[0] + viewport[2]: break
                 if viewport and c_rect[0] + c_rect[2] < viewport[0]: continue
                 self._render_element_at(child, c_rect, viewport)
             return

        self._layout_cache_stats["misses"] += 1
        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        pt = self._resolve_val(raw_padding[0], h); pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h); pl = self._resolve_val(raw_padding[3], w)

        cursor_x = x + pl
        av_w = w - pr - pl; av_h = h - pt - pb

        layout_results = []
        for child in item.get(core.KEY_CHILDREN, []):
            raw_margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
            mt = self._resolve_val(raw_margin[0], av_h)
            ml = self._resolve_val(raw_margin[3], av_w)
            mr = self._resolve_val(raw_margin[1], av_w)

            cw_raw = child.get(core.KEY_RECT, [0,0,0,0])
            cw = self._measure_item_width(child, av_h) if cw_raw[2] == "auto" else self._resolve_val(cw_raw[2], av_w)
            ch = self._measure_item(child, cw, av_h)

            c_rect = (cursor_x + ml, y + pt + mt, cw, ch)
            layout_results.append((c_rect, child))

            if viewport and (cursor_x + ml > viewport[0] + viewport[2]): break
            if viewport and (cursor_x + ml + cw < viewport[0]):
                cursor_x += ml + cw + mr
                continue

            self._render_element_at(child, c_rect, viewport)
            cursor_x += ml + cw + mr

        self._layout_cache[cache_key] = layout_results

    def _render_element_at(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        typ = item.get(core.KEY_TYPE)
        # Route to appropriate handler
        if typ == core.TYPE_VBOX: self._render_vbox(item, rect, viewport)
        elif typ == core.TYPE_HBOX: self._render_hbox(item, rect, viewport)
        else: self.render_item_direct(item, rect)

    def _render_scrollable_layer(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        x, y, w, h = rect
        scroll_y = item.get(core.KEY_SCROLL_Y, 0)

        clip_rect = sdl2.SDL_Rect(x, y, w, h)
        self.primitive_renderer.flush()
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, clip_rect)
        # Use viewport height for children layout, scroll_y shifts content up
        virtual_parent_rect = (x, y - scroll_y, w, h)
        current_viewport = (x, y, w, h)
        for child in item.get(core.KEY_CHILDREN, []):
            self._render_item(child, virtual_parent_rect, current_viewport)
        self.primitive_renderer.flush()
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)

    def _resolve_val(self, val: Union[int, str], parent_len: int) -> int:
        return utils.resolve_val(val, parent_len)

    def _measure_item(self, item: Dict[str, Any], available_width: int, available_height: int = 0) -> int:
        # Height measurement
        typ = item.get(core.KEY_TYPE)
        if typ == core.TYPE_TEXT:
            if item.get(core.KEY_MARKUP, True):
                return self.text_renderer.measure_rich_text_height(item, available_width, available_height)
            return self.text_renderer.measure_plain_text_height(item, available_width, available_height)
        elif typ == core.TYPE_VBOX:
            return self._measure_vbox_height(item, available_width, available_height)
        elif typ == core.TYPE_FLEXBOX:
            # Flex measurement not fully extracted yet?
            # FlexRenderer should handle it?
            # Replicating simple logic or using FlexNode?
            # For simplicity, returning 0 if not auto or using provided height in rect.
            # But flexbox height auto needs calculation.
            # Original code had _measure_flexbox_height.
            return self._measure_flexbox_height(item, available_width, available_height)
        elif typ == core.TYPE_HBOX:
            return self._measure_hbox_height(item, available_width, available_height)

        # Default or fixed height
        raw = item.get(core.KEY_RECT, [0,0,0,0])
        if raw[3] != "auto": return self._resolve_val(raw[3], available_height)
        return 0

    def _measure_item_width(self, item: Dict[str, Any], available_width: int, available_height: int = 0) -> int:
        typ = item.get(core.KEY_TYPE)
        if typ == core.TYPE_TEXT:
             return self.text_renderer.measure_text_width(item.get(core.KEY_TEXT, ""),
                                    item.get(core.KEY_FONT),
                                    item.get(core.KEY_FONT_SIZE, 16))
        elif typ == core.TYPE_HBOX:
             return self._measure_hbox_width(item, available_width, available_height)
        elif typ == core.TYPE_FLEXBOX:
             return self._measure_flexbox_width(item, available_width, available_height)

        raw = item.get(core.KEY_RECT, [0,0,0,0])
        if raw[2] != "auto": return self._resolve_val(raw[2], available_width)
        return 0

    # Measurement Helpers (kept here for now or extract to LayoutEngine?)

    def _measure_vbox_height(self, item: Dict[str, Any], av_w: int, av_h: int) -> int:
        h = 0
        raw_padding = item.get(core.KEY_PADDING, (0,0,0,0))
        pt = self._resolve_val(raw_padding[0], av_h); pb = self._resolve_val(raw_padding[2], av_h)
        h += pt + pb
        # Compute available height for children: if VBox has fixed height, use it
        raw_rect = item.get(core.KEY_RECT, [0, 0, 0, 0])
        if raw_rect[3] != "auto":
            child_av_h = self._resolve_val(raw_rect[3], av_h) - pt - pb
        else:
            child_av_h = av_h
        for child in item.get(core.KEY_CHILDREN, []):
             raw_margin = child.get(core.KEY_MARGIN, (0,0,0,0))
             mt = self._resolve_val(raw_margin[0], child_av_h); mb = self._resolve_val(raw_margin[2], child_av_h)
             cw_raw = child.get(core.KEY_RECT, [0,0,0,0])
             cw = self._resolve_val(cw_raw[2], av_w) # VBox children width usually fixed
             ch = self._measure_item(child, cw, child_av_h)
             h += mt + ch + mb
        return h

    def _measure_hbox_height(self, item: Dict[str, Any], av_w: int, av_h: int) -> int:
        # Compute available height for children: if HBox has fixed height, use it
        raw_rect = item.get(core.KEY_RECT, [0, 0, 0, 0])
        raw_padding = item.get(core.KEY_PADDING, (0,0,0,0))
        pt = self._resolve_val(raw_padding[0], av_h); pb = self._resolve_val(raw_padding[2], av_h)
        if raw_rect[3] != "auto":
            own_h = self._resolve_val(raw_rect[3], av_h)
            child_av_h = own_h - pt - pb
        else:
            child_av_h = av_h
        max_h = 0
        for child in item.get(core.KEY_CHILDREN, []):
             raw_margin = child.get(core.KEY_MARGIN, (0,0,0,0))
             mt = self._resolve_val(raw_margin[0], child_av_h); mb = self._resolve_val(raw_margin[2], child_av_h)
             cw_raw = child.get(core.KEY_RECT, [0,0,0,0])
             cw = self._measure_item_width(child, child_av_h) if cw_raw[2] == "auto" else self._resolve_val(cw_raw[2], av_w)
             ch = self._measure_item(child, cw, child_av_h)
             max_h = max(max_h, mt + ch + mb)
        return max_h + pt + pb

    def _measure_hbox_width(self, item: Dict[str, Any], parent_height: int) -> int:
         # Rough estimation
         w = 0
         for child in item.get(core.KEY_CHILDREN, []):
              w += self._measure_item_width(child, 0, parent_height)
         return w

    def _measure_flexbox_height(self, item: Dict[str, Any], av_w: int, av_h: int) -> int:
         # Defer to FlexRenderer logic?
         # Re-implementing simplified measure loop
         # TODO: Proper flex layout measurement without full tree build if possible.
         # But constructing tree is cheap.
         node = self.flex_renderer._build_flex_tree(item, av_w, av_h)
         node.calculate_layout(av_w, av_h, force_size=False)
         return int(node.layout_rect[3])

    def _measure_flexbox_width(self, item: Dict[str, Any], av_w: int, av_h: int) -> int:
         node = self.flex_renderer._build_flex_tree(item, av_w, av_h)
         node.calculate_layout(av_w, av_h, force_size=False)
         return int(node.layout_rect[2])

    def measure_text_width(self, text: str, font_path: str = None, font_size: int = 16) -> int:
        return self.text_renderer.measure_text_width(text, font_path, font_size)

