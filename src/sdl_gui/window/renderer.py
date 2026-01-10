
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
from sdl_gui.window.spatial_index import SpatialIndex


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
        self._vector_cache: Dict[str, sdl2.ext.Texture] = {}
        self._text_texture_cache: Dict[Tuple, sdl2.ext.Texture] = {}
        self._rich_text_layout_cache: Dict[Tuple, Tuple[List, Dict]] = {}
        self._rounded_box_cache: Dict[str, sdl2.ext.Texture] = {}
        self._measurement_cache: Dict[Tuple[str, int], int] = {}
        
        # Text measurement cache: (font_path, size, text, bold) -> (width, height)
        self._text_measurement_cache: Dict[Tuple, Tuple[int, int]] = {}

        self._render_queue: List[sdl2.SDL_Rect] = []
        self._render_queue_color: Tuple[int, int, int, int] = None

        self._last_window_size = (0, 0)
        self._hit_list: List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]] = []

        self._last_display_list: List[Dict[str, Any]] = []
        self._display_list_lock = threading.Lock()

        # Culling statistics for performance monitoring
        self._culling_stats: Dict[str, int] = {"rendered": 0, "skipped": 0}

        # Dirty rectangles tracking for incremental rendering
        self._prev_display_list: List[Dict[str, Any]] = []
        self._dirty_regions: List[Tuple[int, int, int, int]] = []
        self._dirty_stats: Dict[str, int] = {"full_renders": 0, "partial_renders": 0, "skipped_frames": 0}
        self._incremental_mode: bool = False  # Disabled by default - opt-in via set_incremental_mode()
        self._force_full_render: bool = True  # First frame is always full

        # Layout caching: maps (item_hash, parent_rect) → list of (child_rect, child_item)
        self._layout_cache: Dict[Tuple, List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]]] = {}
        self._layout_cache_stats: Dict[str, int] = {"hits": 0, "misses": 0}

        # Performance profiling
        self._perf_enabled: bool = False
        self._perf_stats: Dict[str, float] = {}
        self._perf_timers: Dict[str, float] = {}
        self._draw_call_count: int = 0
        self._batch_stats: Dict[str, int] = {"batched_rects": 0, "saved_calls": 0}

        # Spatial index for efficient viewport queries
        self._spatial_index = SpatialIndex(max_depth=6)
        
        # Display list hash for caching (avoids deepcopy and spatial index rebuild)
        self._display_list_hash: int = 0
        
        # Flexbox layout cache: (item_hash, w, h) -> FlexNode with calculated layout
        self._flex_layout_cache: Dict[Tuple, Any] = {}
        
        # Markdown parsing cache: (text, default_color) -> parsed segments
        self._markdown_parse_cache: Dict[Tuple, List] = {}
        
        # Rich text height cache: (text, font_path, size, width) -> height
        self._rich_text_height_cache: Dict[Tuple, int] = {}

    def clear(self, color=(0, 0, 0, 0), partial: bool = False):
        """
        Clear the render target.
        
        Args:
            color: The clear color (R, G, B, A).
            partial: If True and incremental mode is active, only clear dirty regions.
        """
        r, g, b, a = color
        sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, r, g, b, a)
        
        if partial and self._incremental_mode and self._dirty_regions and not self._force_full_render:
            # Clear only dirty regions
            for region in self._dirty_regions:
                rx, ry, rw, rh = region
                clear_rect = sdl2.SDL_Rect(int(rx), int(ry), int(rw), int(rh))
                sdl2.SDL_RenderFillRect(self.renderer.sdlrenderer, clear_rect)
        else:
            # Full clear
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

    def get_culling_stats(self) -> Dict[str, int]:
        """
        Return culling statistics from the last render.
        
        Returns:
            Dict with 'rendered' and 'skipped' counts indicating how many
            items were actually rendered vs. skipped due to viewport culling.
        """
        return self._culling_stats.copy()

    def get_dirty_stats(self) -> Dict[str, int]:
        """
        Return dirty rendering statistics.
        
        Returns:
            Dict with 'full_renders', 'partial_renders', and 'skipped_frames' counts.
        """
        return self._dirty_stats.copy()

    def set_incremental_mode(self, enabled: bool) -> None:
        """
        Enable or disable incremental (dirty rectangles) rendering.
        
        Args:
            enabled: True to enable incremental rendering, False for full renders.
        """
        self._incremental_mode = enabled
        if not enabled:
            self._force_full_render = True

    def mark_dirty(self, rect: Tuple[int, int, int, int] = None) -> None:
        """
        Mark a region as dirty, forcing re-render on next frame.
        
        Args:
            rect: The rectangle to mark dirty (x, y, w, h). 
                  If None, marks entire window as dirty.
        """
        if rect is None:
            self._force_full_render = True
        else:
            self._dirty_regions.append(rect)

    def get_layout_cache_stats(self) -> Dict[str, int]:
        """
        Return layout cache statistics.
        
        Returns:
            Dict with 'hits' and 'misses' counts.
        """
        return self._layout_cache_stats.copy()

    def enable_profiling(self, enabled: bool) -> None:
        """
        Enable or disable performance profiling.
        
        When enabled, timing data is collected for various rendering operations.
        
        Args:
            enabled: True to enable profiling, False to disable.
        """
        self._perf_enabled = enabled
        if enabled:
            self._perf_stats = {}
            self._draw_call_count = 0
            self._batch_stats = {"batched_rects": 0, "saved_calls": 0}

    def get_perf_stats(self) -> Dict[str, Any]:
        """
        Return performance statistics from profiling.
        
        Returns:
            Dict containing timing data, draw call counts, and batch statistics.
        """
        return {
            "timings": self._perf_stats.copy(),
            "draw_calls": self._draw_call_count,
            "batch_stats": self._batch_stats.copy(),
            "culling_stats": self._culling_stats.copy(),
            "layout_cache_stats": self._layout_cache_stats.copy(),
            "spatial_index_stats": self._spatial_index.get_stats(),
        }

    def get_spatial_stats(self) -> Dict[str, int]:
        """
        Return spatial index statistics.
        
        Returns:
            Dict with insert, remove, query counts and item totals.
        """
        return self._spatial_index.get_stats()

    def _perf_start(self, name: str) -> None:
        """Start a performance timer."""
        if self._perf_enabled:
            import time
            self._perf_timers[name] = time.perf_counter()

    def _perf_end(self, name: str) -> None:
        """End a performance timer and accumulate the elapsed time."""
        if self._perf_enabled and name in self._perf_timers:
            import time
            elapsed = time.perf_counter() - self._perf_timers[name]
            if name in self._perf_stats:
                self._perf_stats[name] += elapsed
            else:
                self._perf_stats[name] = elapsed
            del self._perf_timers[name]

    def _get_layout_cache_key(self, item: Dict[str, Any], 
                               parent_rect: Tuple[int, int, int, int]) -> Tuple:
        """
        Generate a cache key for layout caching.
        
        The key is based on the item's hash (excluding children, which are 
        handled separately) and the parent rectangle dimensions.
        
        Args:
            item: The container item (VBox/HBox).
            parent_rect: The parent rectangle (x, y, w, h).
            
        Returns:
            A hashable tuple suitable for use as a cache key.
        """
        # Include children hashes in the key since their layout affects results
        children_hash = tuple(self._hash_item(c) for c in item.get(core.KEY_CHILDREN, []))
        return (self._hash_item(item), parent_rect, children_hash)

    def _make_hashable(self, value: Any) -> Any:
        """
        Recursively convert a value to a hashable representation.
        
        Handles nested dicts, lists, and special types like callables.
        """
        if isinstance(value, dict):
            return tuple(sorted((k, self._make_hashable(v)) for k, v in value.items()))
        elif isinstance(value, list):
            return tuple(self._make_hashable(v) for v in value)
        elif isinstance(value, tuple):
            return tuple(self._make_hashable(v) for v in value)
        elif callable(value):
            return id(value)  # Functions by id
        else:
            try:
                hash(value)
                return value
            except TypeError:
                return str(value)  # Fallback for unhashable types

    def _hash_item(self, item: Dict[str, Any]) -> int:
        """
        Generate a hash for a display list item for change detection.
        
        Excludes children from hash as they are compared separately.
        """
        hashable_parts = []
        for key, value in sorted(item.items()):
            if key == core.KEY_CHILDREN:
                continue  # Children are handled separately
            hashable_parts.append((key, self._make_hashable(value)))
        return hash(tuple(hashable_parts))

    def _compute_dirty_regions(self, new_list: List[Dict[str, Any]], 
                                old_list: List[Dict[str, Any]],
                                parent_rect: Tuple[int, int, int, int]) -> List[Tuple[int, int, int, int]]:
        """
        Compare display lists and return list of dirty rectangles.
        
        Args:
            new_list: The new display list.
            old_list: The previous display list.
            parent_rect: The parent rectangle for coordinate resolution.
            
        Returns:
            List of (x, y, w, h) tuples representing dirty regions.
        """
        dirty = []
        px, py, pw, ph = parent_rect
        
        # Quick check: different lengths = consider entire parent dirty
        if len(new_list) != len(old_list):
            return [parent_rect]
        
        for new_item, old_item in zip(new_list, old_list):
            # Get item rects
            new_rect = new_item.get(core.KEY_RECT, [0, 0, pw, ph])
            old_rect = old_item.get(core.KEY_RECT, [0, 0, pw, ph])
            
            # Resolve coordinates
            new_x = px + self._resolve_val(new_rect[0], pw)
            new_y = py + self._resolve_val(new_rect[1], ph)
            new_w = pw if new_rect[2] == "auto" else self._resolve_val(new_rect[2], pw)
            new_h = ph if new_rect[3] == "auto" else self._resolve_val(new_rect[3], ph)
            
            old_x = px + self._resolve_val(old_rect[0], pw)
            old_y = py + self._resolve_val(old_rect[1], ph)
            old_w = pw if old_rect[2] == "auto" else self._resolve_val(old_rect[2], pw)
            old_h = ph if old_rect[3] == "auto" else self._resolve_val(old_rect[3], ph)
            
            new_abs_rect = (new_x, new_y, new_w, new_h)
            old_abs_rect = (old_x, old_y, old_w, old_h)
            
            # Compare item hashes (excluding children)
            if self._hash_item(new_item) != self._hash_item(old_item):
                # Item changed - mark both old and new positions as dirty
                dirty.append(old_abs_rect)
                if old_abs_rect != new_abs_rect:
                    dirty.append(new_abs_rect)
            elif new_abs_rect != old_abs_rect:
                # Position changed - mark both positions as dirty
                dirty.append(old_abs_rect)
                dirty.append(new_abs_rect)
            
            # Recursively check children
            new_children = new_item.get(core.KEY_CHILDREN, [])
            old_children = old_item.get(core.KEY_CHILDREN, [])
            if new_children or old_children:
                child_dirty = self._compute_dirty_regions(new_children, old_children, new_abs_rect)
                dirty.extend(child_dirty)
        
        return dirty

    def _merge_dirty_regions(self, regions: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Merge overlapping dirty regions to reduce clip operations.
        
        Returns a list of non-overlapping rectangles covering all dirty areas.
        """
        if not regions:
            return []
        
        if len(regions) == 1:
            return regions
        
        # Simple approach: compute bounding box of all regions
        # More advanced: use R-tree or spatial partitioning
        min_x = min(r[0] for r in regions)
        min_y = min(r[1] for r in regions)
        max_x = max(r[0] + r[2] for r in regions)  
        max_y = max(r[1] + r[3] for r in regions)
        
        # If merged region is much larger than individual regions, keep separate
        merged_area = (max_x - min_x) * (max_y - min_y)
        total_individual_area = sum(r[2] * r[3] for r in regions)
        
        # If bounding box is less than 2x total area, use bounding box
        if merged_area <= total_individual_area * 2:
            return [(min_x, min_y, max_x - min_x, max_y - min_y)]
        
        # Otherwise keep separate (simplified - just return unique regions)
        seen = set()
        unique = []
        for r in regions:
            if r not in seen:
                seen.add(r)
                unique.append(r)
        return unique

    def _is_visible(self, rect: Tuple[int, int, int, int],
                    viewport: Tuple[int, int, int, int] = None) -> bool:
        """
        Check if a rectangle is visible within the viewport.
        
        Args:
            rect: The rectangle to check (x, y, w, h)
            viewport: The viewport rectangle (vx, vy, vw, vh). If None, always visible.
            
        Returns:
            True if the rectangle intersects with the viewport, False otherwise.
        """
        if viewport is None:
            return True
        
        x, y, w, h = rect
        vx, vy, vw, vh = viewport
        
        # Rectangle intersection test: not visible if completely outside
        return not (x + w <= vx or x >= vx + vw or
                    y + h <= vy or y >= vy + vh)

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
        # Use ARGB8888 as it's common and well-supported for reading pixels
        surface = sdl2.SDL_CreateRGBSurface(0, w, h, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
        sdl2.SDL_RenderReadPixels(self.renderer.sdlrenderer, None,
                                  sdl2.SDL_PIXELFORMAT_ARGB8888,
                                  surface.contents.pixels,
                                  surface.contents.pitch)
        sdl2.SDL_SaveBMP(surface, filename.encode('utf-8'))
        sdl2.SDL_FreeSurface(surface)

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """
        Get the RGBA color of the pixel at (x, y).
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            A tuple of (R, G, B, A)
        """
        rect = sdl2.SDL_Rect(x, y, 1, 1)
        # We use ABGR8888 which, on little-endian systems, results in R, G, B, A byte order in memory.
        pixels = ctypes.create_string_buffer(4)
        sdl2.SDL_RenderReadPixels(
            self.renderer.sdlrenderer,
            rect,
            sdl2.SDL_PIXELFORMAT_ABGR8888,
            pixels,
            4
        )
        
        # In Python 3, pixels.raw is a bytes object
        # RGBA8888 means R is the first byte, then G, then B, then A
        # regardless of endianness when treated as bytes.
        r = pixels.raw[0]
        g = pixels.raw[1]
        b = pixels.raw[2]
        a = pixels.raw[3]
        
        return (r, g, b, a)

    def render_list(self, display_list: List[Dict[str, Any]], force_full: bool = False) -> None:
        """
        Render the display list.
        
        Args:
            display_list: The list of display items to render.
            force_full: If True, force a full render ignoring incremental mode.
        """
        self._perf_start("render_list_total")
        
        width, height = self.window.size
        self.renderer.logical_size = (width, height)
        root_rect = (0, 0, width, height)
        root_viewport = root_rect

        # Check for window resize - invalidates all caches
        if (width, height) != self._last_window_size:
             self._measurement_cache = {}
             self._layout_cache = {}  # Invalidate layout cache on resize
             self._spatial_index.rebuild(bounds=(0, 0, width * 2, height * 2))
             self._last_window_size = (width, height)
             self._force_full_render = True  # Window resize = full render

        # Reset culling statistics
        self._culling_stats = {"rendered": 0, "skipped": 0}

        # Determine if we should use incremental mode
        do_full_render = force_full or self._force_full_render or not self._incremental_mode
        
        if not do_full_render:
            # Compute dirty regions by comparing with previous display list
            self._dirty_regions = self._compute_dirty_regions(
                display_list, self._prev_display_list, root_rect
            )
            self._dirty_regions = self._merge_dirty_regions(self._dirty_regions)
            
            if not self._dirty_regions:
                # Nothing changed - skip rendering entirely
                self._dirty_stats["skipped_frames"] += 1
                self._perf_end("render_list_total")
                return
            
            self._dirty_stats["partial_renders"] += 1
            
            # Set clip to bounding box of dirty regions for rendering
            if len(self._dirty_regions) == 1:
                dr = self._dirty_regions[0]
                clip_rect = sdl2.SDL_Rect(int(dr[0]), int(dr[1]), int(dr[2]), int(dr[3]))
                sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, clip_rect)
                
                # Clear only dirty region
                r, g, b, a = 0, 0, 0, 0  # Clear color
                sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, r, g, b, a)
                sdl2.SDL_RenderFillRect(self.renderer.sdlrenderer, clip_rect)
        else:
            self._dirty_stats["full_renders"] += 1
            self._dirty_regions = [root_rect]  # Entire window is dirty
            self._force_full_render = False  # Reset for next frame

        # Reset hit list for this frame
        self._hit_list = []

        # Store for debug dump and next frame comparison
        with self._display_list_lock:
            self._last_display_list = display_list
        
        # Compute display list hash for dirty detection and spatial index caching
        # Using hash of string representation instead of deepcopy (much faster)
        current_display_hash = hash(str(display_list))
        display_list_changed = current_display_hash != self._display_list_hash
        self._display_list_hash = current_display_hash
        
        # Store for next frame dirty detection (incremental mode)
        # Note: We now use hash for spatial index but still need list for _compute_dirty_regions
        self._prev_display_list = display_list

        # Clear and rebuild spatial index only if display list changed
        self._perf_start("spatial_index_build")
        if display_list_changed:
            self._spatial_index.clear()
            self._build_spatial_index(display_list, root_rect)
        self._perf_end("spatial_index_build")

        # Render items (viewport culling will skip items outside dirty regions too)
        self._perf_start("render_items")
        for item in display_list:
            self._render_item(item, root_rect, root_viewport)
        self._perf_end("render_items")

        self._flush_render_queue()
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)
        
        self._perf_end("render_list_total")

    def _build_spatial_index(
        self,
        items: List[Dict[str, Any]],
        parent_rect: Tuple[int, int, int, int],
        prefix: str = ""
    ) -> None:
        """
        Build the spatial index from the display list.
        
        Args:
            items: List of display items.
            parent_rect: Parent rectangle for coordinate resolution.
            prefix: Item ID prefix for uniqueness.
        """
        px, py, pw, ph = parent_rect
        
        for idx, item in enumerate(items):
            item_id = f"{prefix}{idx}"
            raw_rect = item.get(core.KEY_RECT)
            
            if raw_rect:
                if raw_rect[2] == "auto":
                    rw = self._measure_item_width(item, ph)
                else:
                    rw = self._resolve_val(raw_rect[2], pw)
                
                if raw_rect[3] == "auto":
                    rh = self._measure_item(item, rw, ph)
                else:
                    rh = self._resolve_val(raw_rect[3], ph)
                
                rx = self._resolve_val(raw_rect[0], pw)
                ry = self._resolve_val(raw_rect[1], ph)
                current_rect = (px + rx, py + ry, rw, rh)
            else:
                current_rect = parent_rect
            
            # Insert into spatial index
            self._spatial_index.insert(item_id, current_rect)
            
            # Recursively index children
            children = item.get(core.KEY_CHILDREN, [])
            if children:
                self._build_spatial_index(children, current_rect, f"{item_id}_")

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
        elif item_type == core.TYPE_VECTOR_GRAPHICS:
            self._flush_render_queue()
            self._render_vector_graphics(item, rect)
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

        # Early culling: skip items that are completely outside the viewport
        if not self._is_visible(current_rect, viewport):
            self._culling_stats["skipped"] += 1
            return

        self._culling_stats["rendered"] += 1
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
        elif item_type == core.TYPE_VECTOR_GRAPHICS:
            self._render_vector_graphics(item, current_rect)

    def _render_flexbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        """Render a FlexBox item by building a FlexNode tree and resolving layout."""
        x, y, w, h = rect
        
        # Check flexbox layout cache
        flex_cache_key = (self._hash_item(item), w, h, x, y)
        cached_node = self._flex_layout_cache.get(flex_cache_key)
        
        if cached_node is not None:
            root_node = cached_node
        else:
            # 1. Build Flex Tree
            root_node = self._build_flex_tree(item, w, h)
            
            # 2. Calculate Layout
            root_node.calculate_layout(w, h, x_offset=x, y_offset=y, force_size=True)
            
            # Cache the result
            self._flex_layout_cache[flex_cache_key] = root_node
        
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
        """Render flex node children with viewport culling."""
        for i, child_node in enumerate(node.children):
            if hasattr(child_node, 'original_item'):
                 child_item = child_node.original_item
            else:
                 continue
            
            cx, cy, cw, ch = child_node.layout_rect
            child_rect = (int(cx), int(cy), int(cw), int(ch))
            
            # Viewport culling check
            if not self._is_visible(child_rect, viewport):
                self._culling_stats["skipped"] += 1
                continue
            
            self._culling_stats["rendered"] += 1
            
            if child_item.get(core.KEY_TYPE) == core.TYPE_FLEXBOX:
                 self._render_flex_node_tree_pass(child_node, viewport)
            else:
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
        
        self._perf_start("flush_queue")
        count = len(self._render_queue)
        
        # Track batching stats
        if self._perf_enabled:
            self._batch_stats["batched_rects"] += count
            self._batch_stats["saved_calls"] += count - 1  # Saved (count-1) calls
            self._draw_call_count += 1  # One actual draw call for all rects
        
        rects_array = (sdl2.SDL_Rect * count)(*self._render_queue)
        r, g, b, a = self._render_queue_color
        sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, r, g, b, a)
        sdl2.SDL_RenderFillRects(self.renderer.sdlrenderer, rects_array, count)
        self._render_queue = []
        self._render_queue_color = None
        
        self._perf_end("flush_queue")

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
        if w <= 0 or h <= 0: return

        # Try to use cached texture for rounded box
        cache_key = f"rbox_{w}_{h}_{radius}_{color}"
        texture = self._rounded_box_cache.get(cache_key)
        
        if not texture:
             texture = self._create_rounded_box_texture(w, h, radius, color)
             if texture:
                 self._rounded_box_cache[cache_key] = texture
        
        if texture:
             self.renderer.copy(texture, dstrect=(x, y, w, h))
             return

        # Fallback to direct drawing (slow)
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

    def _create_rounded_box_texture(self, w: int, h: int, radius: int, color: Tuple[int, int, int, int]) -> Union[sdl2.ext.Texture, None]:
        sdl_renderer = self.renderer.sdlrenderer
        
        # Create target texture
        target = sdl2.SDL_CreateTexture(sdl_renderer, sdl2.SDL_PIXELFORMAT_RGBA8888, 
                                        sdl2.SDL_TEXTUREACCESS_TARGET, w, h)
        if not target: return None
        
        sdl2.SDL_SetTextureBlendMode(target, sdl2.SDL_BLENDMODE_BLEND)
        
        old_target = sdl2.SDL_GetRenderTarget(sdl_renderer)
        sdl2.SDL_SetRenderTarget(sdl_renderer, target)
        
        sdl2.SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0, 0)
        sdl2.SDL_RenderClear(sdl_renderer)
        
        # Draw the rounded box using the same code but to texture
        # Recursive call to _draw_aa_rounded_box? No, infinite recursion.
        # Use direct drawing logic here.
        gfx_color = self._to_sdlgfx_color(color)

        sdlgfx.roundedBoxColor(sdl_renderer, 0, 0, w - 1, h - 1, radius, gfx_color)
        # Add AA borders manually as in original code
        sdlgfx.aalineColor(sdl_renderer, radius, 0, w - 1 - radius, 0, gfx_color)
        sdlgfx.aalineColor(sdl_renderer, radius, h - 1, w - 1 - radius, h - 1, gfx_color)
        sdlgfx.aalineColor(sdl_renderer, 0, radius, 0, h - 1 - radius, gfx_color)
        sdlgfx.aalineColor(sdl_renderer, w - 1, radius, w - 1, h - 1 - radius, gfx_color)

        def set_clip(cx, cy, cw, ch):
             clip = sdl2.SDL_Rect(cx, cy, cw, ch)
             sdl2.SDL_RenderSetClipRect(sdl_renderer, ctypes.byref(clip))

        set_clip(0, 0, radius, radius); sdlgfx.aacircleColor(sdl_renderer, radius, radius, radius, gfx_color)
        set_clip(w - radius, 0, radius, radius); sdlgfx.aacircleColor(sdl_renderer, w - 1 - radius, radius, radius, gfx_color)
        set_clip(w - radius, h - radius, radius, radius); sdlgfx.aacircleColor(sdl_renderer, w - 1 - radius, h - 1 - radius, radius, gfx_color)
        set_clip(0, h - radius, radius, radius); sdlgfx.aacircleColor(sdl_renderer, radius, h - 1 - radius, radius, gfx_color)
        sdl2.SDL_RenderSetClipRect(sdl_renderer, None)

        sdl2.SDL_SetRenderTarget(sdl_renderer, old_target)
        return RawTexture(self.renderer, target)


    def _render_vbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        x, y, w, h = rect
        if item.get(core.KEY_COLOR): self._draw_rect_primitive(item, rect)

        # Check layout cache
        cache_key = self._get_layout_cache_key(item, rect)
        cached_layout = self._layout_cache.get(cache_key)
        
        if cached_layout is not None:
            # Cache hit: use cached child positions
            self._layout_cache_stats["hits"] += 1
            for c_rect, child in cached_layout:
                child_top = c_rect[1]
                child_bottom = child_top + c_rect[3]
                
                if viewport and child_top > viewport[1] + viewport[3]:
                    remaining = len(cached_layout) - cached_layout.index((c_rect, child))
                    self._culling_stats["skipped"] += remaining
                    break
                if viewport and child_bottom < viewport[1]:
                    self._culling_stats["skipped"] += 1
                    continue
                
                self._culling_stats["rendered"] += 1
                self._render_element_at(child, c_rect, viewport)
            return

        # Cache miss: compute layout
        self._layout_cache_stats["misses"] += 1
        
        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        pt = self._resolve_val(raw_padding[0], h)
        pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h)
        pl = self._resolve_val(raw_padding[3], w)

        cursor_y = y + pt
        av_w = w - pr - pl
        av_h = h - pt - pb

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
            
            child_top = cursor_y + mt
            child_bottom = child_top + ch

            if viewport and child_top > viewport[1] + viewport[3]:
                remaining = len(item.get(core.KEY_CHILDREN, [])) - item.get(core.KEY_CHILDREN, []).index(child)
                self._culling_stats["skipped"] += remaining
                break
            if viewport and child_bottom < viewport[1]:
                self._culling_stats["skipped"] += 1
                cursor_y += mt + ch + mb
                continue

            self._culling_stats["rendered"] += 1
            self._render_element_at(child, c_rect, viewport)
            cursor_y += mt + ch + mb

        # Store in cache
        self._layout_cache[cache_key] = layout_results

    def _render_hbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        x, y, w, h = rect
        if item.get(core.KEY_COLOR): self._draw_rect_primitive(item, rect)

        # Check layout cache
        cache_key = self._get_layout_cache_key(item, rect)
        cached_layout = self._layout_cache.get(cache_key)
        
        if cached_layout is not None:
            # Cache hit: use cached child positions
            self._layout_cache_stats["hits"] += 1
            for c_rect, child in cached_layout:
                child_left = c_rect[0]
                child_right = child_left + c_rect[2]
                
                if viewport and child_left > viewport[0] + viewport[2]:
                    remaining = len(cached_layout) - cached_layout.index((c_rect, child))
                    self._culling_stats["skipped"] += remaining
                    break
                if viewport and child_right < viewport[0]:
                    self._culling_stats["skipped"] += 1
                    continue
                
                self._culling_stats["rendered"] += 1
                self._render_element_at(child, c_rect, viewport)
            return

        # Cache miss: compute layout
        self._layout_cache_stats["misses"] += 1

        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        pt = self._resolve_val(raw_padding[0], h)
        pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h)
        pl = self._resolve_val(raw_padding[3], w)

        cursor_x = x + pl
        av_w = w - pr - pl
        av_h = h - pt - pb

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
            
            child_left = cursor_x + ml
            child_right = child_left + cw

            if viewport and child_left > viewport[0] + viewport[2]:
                remaining = len(item.get(core.KEY_CHILDREN, [])) - item.get(core.KEY_CHILDREN, []).index(child)
                self._culling_stats["skipped"] += remaining
                break
            if viewport and child_right < viewport[0]:
                self._culling_stats["skipped"] += 1
                cursor_x += ml + cw + mr
                continue

            self._culling_stats["rendered"] += 1
            self._render_element_at(child, c_rect, viewport)
            cursor_x += ml + cw + mr

        # Store in cache
        self._layout_cache[cache_key] = layout_results

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
        elif typ == core.TYPE_VECTOR_GRAPHICS:
             self._render_vector_graphics(item, rect)

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

    def _measure_text_cached(
        self, text: str, font_path: str, size: int, bold: bool = False
    ) -> Tuple[int, int]:
        """
        Measure text dimensions with caching.
        
        Uses a cache to avoid expensive TTF_RenderUTF8_Blended calls
        for repeated measurements of the same text.
        
        Args:
            text: The text string to measure.
            font_path: Path to the font file.
            size: Font size in pixels.
            bold: Whether the text is bold.
            
        Returns:
            Tuple of (width, height) in pixels.
        """
        cache_key = (font_path, size, text, bold)
        cached = self._text_measurement_cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Use a neutral color for measurement - color doesn't affect dimensions
        fm = self._get_font_manager(font_path, size, (0, 0, 0, 255), bold)
        if fm:
            surface = fm.render(text)
            result = (surface.w, surface.h) if surface else (0, 0)
        else:
            result = (0, 0)
        
        self._text_measurement_cache[cache_key] = result
        return result

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
        text_content = item.get(core.KEY_TEXT, "")
        
        # Check cache
        cache_key = (text_content, rect[2], font_path, size, base_color)
        cached = self._rich_text_layout_cache.get(cache_key)
        if cached:
            return cached

        parser = markdown.MarkdownParser(default_color=base_color)
        segments = parser.parse(text_content)

        def measure_chunk(text_str, seg):
            return self._measure_text_cached(text_str, font_path, size, seg.bold)

        lines = self._wrap_rich_text(segments, measure_chunk, rect[2], item.get(core.KEY_WRAP, True))
        _, lh = measure_chunk("Tg", segments[0] if segments else None)
        line_height = lh if lh > 0 else size

        settings = {"font_path": font_path, "size": size, "line_h": line_height}
        self._rich_text_layout_cache[cache_key] = (lines, settings)
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
        
        if isinstance(source, str):
            return img.IMG_Load(source.encode('utf-8'))
        elif isinstance(source, bytes):
            rw = sdl2.SDL_RWFromConstMem(source, len(source))
            return img.IMG_Load_RW(rw, 1)
        elif callable(source):
            # Dynamic source? Not supported yet in this simple loader
            return None
        return None

    def _render_vector_graphics(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
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
             self._flush_render_queue()
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
        pt = self._resolve_val(raw_padding[0], h)
        pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h)
        pl = self._resolve_val(raw_padding[3], w)
        
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
        
        sdl2.SDL_SetTextureBlendMode(texture, sdl2.SDL_BLENDMODE_BLEND)
        return RawTexture(self.renderer, texture)

    def _execute_vector_commands(self, commands: List[Dict[str, Any]], w: int, h: int, 
                                 content_w: int = None, content_h: int = None, 
                                 offset_x: int = 0, offset_y: int = 0,
                                 renderer_override=None, scale_factor: int = 1):
        renderer = renderer_override if renderer_override else self.renderer.sdlrenderer
        
        cw = content_w if content_w is not None else w
        ch = content_h if content_h is not None else h
        
        def res_x(val): return self._resolve_val(val, cw) + offset_x
        def res_y(val): return self._resolve_val(val, ch) + offset_y
        def res_w(val): return self._resolve_val(val, cw)
        def res_h(val): return self._resolve_val(val, ch)
        def res_r(val): return self._resolve_val(val, min(cw, ch)) # Helper for radius? Or just use one dim?

        # State
        stroke_color = self._to_sdlgfx_color((255, 255, 255, 255)) # Default white
        stroke_color_t = (255, 255, 255, 255)
        fill_color = None
        fill_color_t = None
        current_x, current_y = offset_x, offset_y # Start at 0,0 relative to content
        stroke_width = 1 * scale_factor  # Scale stroke width for supersampling

        for cmd in commands:
            ctype = cmd.get(core.CMD_TYPE)
            
            if ctype == core.CMD_STROKE:
                 c = cmd.get("color", (255, 255, 255, 255))
                 stroke_color_t = c if len(c) == 4 else (*c, 255)
                 stroke_color = self._to_sdlgfx_color(c)
                 stroke_width = cmd.get("width", 1) * scale_factor  # Scale for supersampling
                 
            elif ctype == core.CMD_FILL:
                 c = cmd.get("color")
                 if c:
                     fill_color_t = c if len(c) == 4 else (*c, 255)
                     fill_color = self._to_sdlgfx_color(c)
                 else:
                     fill_color = None
                     fill_color_t = None

            elif ctype == core.CMD_MOVE_TO:
                 current_x = res_x(cmd.get("x", 0))
                 current_y = res_y(cmd.get("y", 0))

            elif ctype == core.CMD_LINE_TO:
                 tx = res_x(cmd.get("x", 0)); ty = res_y(cmd.get("y", 0))
                 if stroke_width == 1:
                     # Use anti-aliased line for 1px
                     sdlgfx.aalineColor(renderer, int(current_x), int(current_y), int(tx), int(ty), stroke_color)
                 else:
                     # For thick lines, draw multiple AA lines to simulate thickness
                     # or use thickLineColor (no AA version available)
                     sdlgfx.thickLineColor(renderer, int(current_x), int(current_y), int(tx), int(ty), stroke_width, stroke_color)
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
                          # Use AA lines for rectangle outline
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
            
            elif ctype == core.CMD_CURVE_TO:
                  cx1 = res_x(cmd.get("cx1")); cy1 = res_y(cmd.get("cy1"))
                  cx2 = res_x(cmd.get("cx2")); cy2 = res_y(cmd.get("cy2"))
                  tx = res_x(cmd.get("x")); ty = res_y(cmd.get("y"))
                  sdlgfx.bezierColor(renderer, 
                      (ctypes.c_short * 4)(int(current_x), int(cx1), int(cx2), int(tx)),
                      (ctypes.c_short * 4)(int(current_y), int(cy1), int(cy2), int(ty)),
                      4, 100, stroke_color) 
                  current_x, current_y = tx, ty


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
                 w, _ = self._measure_text_cached(seg.text, font_path, size, seg.bold)
                 total_w += w
             return total_w
        else:
             w, _ = self._measure_text_cached(text, font_path, size, False)
             return w

    def _measure_text_height(self, item: Dict[str, Any], width: int, parent_height: int = 0) -> int:
        if item.get(core.KEY_MARKUP, True): return self._measure_rich_text_height(item, width, parent_height)
        else: return 20

    def _measure_rich_text_height(self, item: Dict[str, Any], width: int, parent_height: int) -> int:
        text = item.get(core.KEY_TEXT, "")
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        size = self._get_resolved_font_size(item, parent_height)
        default_color = item.get(core.KEY_COLOR, (0,0,0,255))

        # Check height cache first (Optimization 7)
        height_cache_key = (text, font_path, size, width, default_color)
        cached_height = self._rich_text_height_cache.get(height_cache_key)
        if cached_height is not None:
            return cached_height

        # Check markdown parsing cache (Optimization 6)
        parse_cache_key = (text, default_color)
        cached_segments = self._markdown_parse_cache.get(parse_cache_key)
        if cached_segments is not None:
            segments = cached_segments
        else:
            parser = markdown.MarkdownParser(default_color=default_color)
            segments = parser.parse(text)
            self._markdown_parse_cache[parse_cache_key] = segments

        def measure_chunk(t, s):
            return self._measure_text_cached(t, font_path, size, s.bold)

        lines = self._wrap_rich_text(segments, measure_chunk, width, True)
        _, lh = measure_chunk("Tg", segments[0] if segments else None)
        line_height = lh if lh > 0 else size
        result = len(lines) * line_height
        
        # Cache the result
        self._rich_text_height_cache[height_cache_key] = result
        return result

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
