import sdl2
import sdl2.ext
from sdl2 import sdlgfx
from typing import List, Dict, Any, Tuple, Union, Callable
from sdl_gui import core, markdown
from sdl2 import sdlttf
import ctypes
import time
from sdl_gui import context
from sdl2 import sdlimage as img


class Window:
    """SDL Window wrapper that renders a display list."""
    
    def __init__(self, title: str, width: int, height: int, debug: bool = False, renderer_flags: int = sdl2.SDL_RENDERER_ACCELERATED):
        sdl2.ext.init()
        try:
            # Attempt to initialize TTF
            from sdl2 import sdlttf
            sdlttf.TTF_Init()
            self.ttf_available = True
        except ImportError:
            print("Warning: SDL_ttf not available. Text rendering disabled.")
            self.ttf_available = False
        except Exception as e:
            print(f"Warning: Failed to initialize SDL_ttf: {e}")
            self.ttf_available = False

        self.window = sdl2.ext.Window(title, size=(width, height), flags=sdl2.SDL_WINDOW_RESIZABLE)
        # Enable Hardware Acceleration for smoother rendering
        self.renderer = sdl2.ext.Renderer(self.window, flags=renderer_flags)
        
        # Hit list for event handling (list of tuples: (rect, item_data))
        self._hit_list: List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]] = []
        
        # Font cache: key -> FontManager
        self._font_cache: Dict[str, sdl2.ext.FontManager] = {}

        # Image cache: key -> Texture
        self._image_cache: Dict[str, sdl2.ext.Texture] = {}
        
        # Text Texture Cache: (font_path, size, color, text) -> Texture
        self._text_texture_cache: Dict[Tuple, sdl2.ext.Texture] = {}
        
        # Render Queue for Batching: list of SDL_Rect with same color
        self._render_queue: List[sdl2.SDL_Rect] = []
        self._render_queue_color: Tuple[int, int, int, int] = None
        
        # Measurement Cache: (id, width) -> height
        self._measurement_cache: Dict[Tuple[str, int], int] = {}
        self._last_window_size = (width, height)


        self.width = width
        self.height = height
        self.debug = debug
        self.fps_start = time.time()
        self.frame_count = 0
        self.current_fps = 0
        
    def __enter__(self):
        """Enter context: return self and potentially set self as a context root."""      
        context.push_parent(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        context.pop_parent()

    def add_child(self, child: Any) -> None:
        """Allow adding children directly to window (e.g. for implicit context)."""
        if not hasattr(self, 'root_children'):
            self.root_children = []
        self.root_children.append(child)
        
    def get_root_display_list(self) -> List[Dict[str, Any]]:
        """Helper to get data from root children if used in retained mode way."""
        if hasattr(self, 'root_children'):
            return [child.to_data() for child in self.root_children]
        return []

    def show(self):
        """Show the window."""
        self.window.show()

    def save_screenshot(self, filename: str) -> None:
        """Save the current window content to a BMP file."""
        w, h = self.window.size
        surface = sdl2.SDL_CreateRGBSurface(0, w, h, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
        sdl2.SDL_RenderReadPixels(self.renderer.sdlrenderer, None, 
                                  sdl2.SDL_PIXELFORMAT_ARGB8888, 
                                  surface.contents.pixels, 
                                  surface.contents.pitch)
        sdl2.SDL_SaveBMP(surface, filename.encode('utf-8'))
        sdl2.SDL_FreeSurface(surface)

    def render(self, display_list: List[Dict[str, Any]]) -> None:
        """Render the display list."""
        self.renderer.clear()
        
        # Determine current window size (in case of resize)
        # Use dynamic size from SDL window
        width, height = self.window.size
        
        # Sync logical size to avoid scaling artifacts
        self.renderer.logical_size = (width, height)
        
        root_rect = (0, 0, width, height)

        # Clear measurement cache if window width changed significantly (reflows)
        # Actually, we key by width, so it's safe. But maybe clear periodically to avoid memory leak?
        # For now, let's just clear if width changes to keep it simple and clean.
        if (width, height) != self._last_window_size:
             self._measurement_cache = {}
             self._last_window_size = (width, height)

        # Clear hit list for this frame
        self._hit_list = []

        for item in display_list:
            self._render_item(item, root_rect)
            
        # Flush any remaining items
        self._flush_render_queue()
            
        # Reset clipping to be safe
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)
        
        # Debug FPS
        if self.debug:
            self.frame_count += 1
            now = time.time()
            if now - self.fps_start >= 1.0:
                self.current_fps = self.frame_count
                self.frame_count = 0
                self.fps_start = now
            
            # Simple direct text rendering for debug overlay
            debug_item = {
                core.KEY_TYPE: core.TYPE_TEXT,
                core.KEY_TEXT: f"FPS: {self.current_fps}",
                core.KEY_COLOR: (0, 255, 0, 255),
                core.KEY_FONT_SIZE: 16
            }
            # Avoid infinite caching of unique FPS strings if possible, or accept cache churn?
            # Actually, FPS numbers change every second, so 60-100 variants per minute. It's fine.
            self._render_text(debug_item, (10, 10, 100, 20))
            self._flush_render_queue()

        self.renderer.present()

    def get_ui_events(self) -> List[Dict[str, Any]]:
        """
        Process SDL events and translate them into UI events based on hit tests.
        Returns a list of high-level UI events (e.g. {'type': 'click', 'target': 'id'}).
        """
        sdl_events = sdl2.ext.get_events()
        ui_events = []
        
        for event in sdl_events:
            # Handle Quit
            if event.type == sdl2.SDL_QUIT:
                ui_events.append({"type": core.EVENT_QUIT})

            # Handle Scroll (Mouse Wheel)
            if event.type == sdl2.SDL_MOUSEWHEEL:
                # Use current event mouse state if possible, or query global state
                # In most SDL apps, mouse position is available via SDL_GetMouseState
                x, y = ctypes.c_int(0), ctypes.c_int(0)
                sdl2.mouse.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
                mx, my = x.value, y.value
                # Find hovered item that listens to SCROLL
                scroll_target = self._find_hit(mx, my, core.EVENT_SCROLL)
                if scroll_target:
                    # Emit SCROLL event
                    # Delta: event.wheel.y (positive is up/away from user, usually -> scroll up content (view goes up))
                    # Standard behavior: Wheel UP (pos) -> Move content DOWN (show top). 
                    # Scroll Y usually represents the top offset.
                    # So Wheel UP -> decrease scroll_y.
                    dy = event.wheel.y
                    
                    # We send the delta primarily.
                    ui_events.append({
                        "type": core.EVENT_SCROLL,
                        "target": scroll_target.get(core.KEY_ID),
                        "delta": dy,
                        # Pass current scroll state if available for convenience
                        "current_scroll_y": scroll_target.get(core.KEY_SCROLL_Y, 0)
                    })

            # Handle Click
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                mx, my = event.button.x, event.button.y
                # Pass the event type we are looking for (CLICK)
                clicked_item = self._find_hit(mx, my, core.EVENT_CLICK)
                
                if clicked_item:
                    # Check if it's a link
                    if clicked_item.get("type") == "link":
                         ui_events.append({
                             "type": core.EVENT_LINK_CLICK,
                             "target": clicked_item.get("target")
                         })
                    else:
                        item_id = clicked_item.get(core.KEY_ID)
                        if item_id:
                            ui_events.append({
                                "type": core.EVENT_CLICK,
                                "target": item_id
                            })

        return ui_events

    def _find_hit(self, mx: int, my: int, required_event: str) -> Dict[str, Any]:
        """
        Find the top-most item at (mx, my) that listens to required_event.
        Returns None if no listening item is found.
        """
        # Iterate in reverse to find top-most element first
        for rect, item in reversed(self._hit_list):
            x, y, w, h = rect
            if x <= mx < x + w and y <= my < y + h:
                # Check if this item listens to the required event
                listen_events = item.get(core.KEY_LISTEN_EVENTS, [])
                if required_event in listen_events:
                    return item
        return None

    def _flush_render_queue(self):
        """Draw all queued rectangles with the current batch color."""
        if not self._render_queue:
            return
            
        # SDL2 requires array of SDL_Rect
        count = len(self._render_queue)
        rects_array = (sdl2.SDL_Rect * count)(*self._render_queue)
        
        # Set color
        r, g, b, a = self._render_queue_color
        sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, r, g, b, a)
        
        # Draw all
        sdl2.SDL_RenderFillRects(self.renderer.sdlrenderer, rects_array, count)
        
        # Clear
        self._render_queue = []
        self._render_queue_color = None

    def _resolve_val(self, val: Union[int, str], parent_len: int) -> int:
        """Resolve a value (int or percentage string) to pixels."""
        if isinstance(val, int):
            return val
        elif isinstance(val, str):
            if val.endswith("%"):
                try:
                    pct = float(val[:-1])
                    return int(parent_len * (pct / 100))
                except ValueError:
                    return 0
            elif val.endswith("px"):
                try:
                    return int(val[:-2])
                except ValueError:
                    return 0
            else:
                 # Try parsing as plain int string
                 try:
                     return int(val)
                 except ValueError:
                     return 0
        return 0

    def _resolve_rect(self, rect_data: List[Any], parent_rect: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """Resolve a rect relative to parent."""
        px, py, pw, ph = parent_rect
        rx = self._resolve_val(rect_data[0], pw)
        ry = self._resolve_val(rect_data[1], ph)
        rw = self._resolve_val(rect_data[2], pw)
        rh = self._resolve_val(rect_data[3], ph)
        
        # X and Y are relative to parent origin
        return (px + rx, py + ry, rw, rh)


    def _render_item(self, item: Dict[str, Any], parent_rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        """Render a single item recursively."""
      
        raw_rect = item.get(core.KEY_RECT)
        current_rect = parent_rect
        
        if raw_rect:
            # Handle auto height/width if present
            px, py, pw, ph = parent_rect
            
            # Resolve Width
            if raw_rect[2] == "auto":
                 rw = self._measure_item_width(item, ph) # Width might depend on height? usually not for text but...
            else:
                 rw = self._resolve_val(raw_rect[2], pw)
                 
            # Resolve Height
            if raw_rect[3] == "auto":
                rh = self._measure_item(item, rw, ph)
            else:
                rh = self._resolve_val(raw_rect[3], ph)

            rx = self._resolve_val(raw_rect[0], pw)
            ry = self._resolve_val(raw_rect[1], ph)
            current_rect = (px + rx, py + ry, rw, rh)

        # CAPTURE HIT (Register this item for event handling)
        # We store the resolved absolute rect and the item data
        self._hit_list.append((current_rect, item))

        item_type = item.get(core.KEY_TYPE)
        
        if item_type == core.TYPE_LAYER:
            children = item.get(core.KEY_CHILDREN, [])
            for child in children:
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

    def _to_sdlgfx_color(self, color: Tuple[int, int, int, int]) -> int:
        """Convert RGBA tuple to ABGR packed integer for Little Endian sdlgfx."""
        r, g, b, a = color
        # 0xAABBGGRR
        return (a << 24) | (b << 16) | (g << 8) | r

    def _draw_rect_primitive(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], raw_rect_check: Any = True) -> None:
        """Helper to draw a rectangle with optional radius and border."""
        if not raw_rect_check: return
        
        # Ensure 4-component tuple (default fallback)
        color = item.get("color")
        if not color: color = (255, 255, 255, 255)
        elif len(color) == 3: color = (*color, 255)
        
        radius = item.get(core.KEY_RADIUS, 0)
        border_color = item.get(core.KEY_BORDER_COLOR)
        border_width = item.get(core.KEY_BORDER_WIDTH, 0)

        x, y, w, h = rect
        
        # Draw filled rectangle
        if radius > 0:
            self._flush_render_queue() # Draw before rounded
            self._draw_aa_rounded_box(rect, radius, color)
        else:
             # Basic Rect - Attempt Batching
             r, g, b, a = color
             
             # If color matches current batch, add to queue
             if self._render_queue_color == color:
                 self._render_queue.append(sdl2.SDL_Rect(x, y, w, h))
             else:
                 # Flush previous batch
                 self._flush_render_queue()
                 # Start new batch
                 self._render_queue_color = color
                 self._render_queue.append(sdl2.SDL_Rect(x, y, w, h))
        
        # Draw border if needed
        if border_width > 0 and border_color:
            if len(border_color) == 3: border_color = (*border_color, 255)
            
            # Simple border
            if radius <= 0:
                self._flush_render_queue() # Draw queued fills first
                b_color = sdl2.ext.Color(*border_color)
                for i in range(border_width):
                     self.renderer.draw_rect((x+i, y+i, w-2*i, h-2*i), b_color)
            else:
                # Rounded border
                self._flush_render_queue() # Draw queued fills first
                gfx_b_color = self._to_sdlgfx_color(border_color)
                for i in range(border_width):
                     bx, by = x + i, y + i
                     bw, bh = w - 2 * i, h - 2 * i
                     if bw <= 0 or bh <= 0: break
                     current_radius = max(0, radius - i)
                     if current_radius > 0:
                         sdlgfx.roundedRectangleColor(self.renderer.sdlrenderer, bx, by, bx+bw-1, by+bh-1, current_radius, gfx_b_color)
                     else:
                         self.renderer.draw_rect((bx, by, bw, bh), sdl2.ext.Color(*border_color))

    def _draw_aa_rounded_box(self, rect: Tuple[int, int, int, int], radius: int, color: Tuple[int, int, int, int]) -> None:
        """Draw an anti-aliased rounded box."""
        x, y, w, h = rect
        gfx_color = self._to_sdlgfx_color(color)
        
        # 1. Fill (Aliased)
        sdlgfx.roundedBoxColor(self.renderer.sdlrenderer, x, y, x + w - 1, y + h - 1, radius, gfx_color)
        
        # 2. AA Edges
        # Top
        sdlgfx.aalineColor(self.renderer.sdlrenderer, x + radius, y, x + w - 1 - radius, y, gfx_color)
        # Bottom
        sdlgfx.aalineColor(self.renderer.sdlrenderer, x + radius, y + h - 1, x + w - 1 - radius, y + h - 1, gfx_color)
        # Left
        sdlgfx.aalineColor(self.renderer.sdlrenderer, x, y + radius, x, y + h - 1 - radius, gfx_color)
        # Right
        sdlgfx.aalineColor(self.renderer.sdlrenderer, x + w - 1, y + radius, x + w - 1, y + h - 1 - radius, gfx_color)
        
        # 3. AA Corners with Clipping
        # Helper for clip setting
        def set_clip(cx, cy, cw, ch):
             clip = sdl2.SDL_Rect(cx, cy, cw, ch)
             sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, ctypes.byref(clip))
             
        # Top-Left
        set_clip(x, y, radius, radius)
        sdlgfx.aacircleColor(self.renderer.sdlrenderer, x + radius, y + radius, radius, gfx_color)
        
        # Top-Right
        set_clip(x + w - radius, y, radius, radius)
        sdlgfx.aacircleColor(self.renderer.sdlrenderer, x + w - 1 - radius, y + radius, radius, gfx_color)
        
        # Bottom-Right
        set_clip(x + w - radius, y + h - radius, radius, radius)
        sdlgfx.aacircleColor(self.renderer.sdlrenderer, x + w - 1 - radius, y + h - 1 - radius, radius, gfx_color)
        
        # Bottom-Left
        set_clip(x, y + h - radius, radius, radius)
        sdlgfx.aacircleColor(self.renderer.sdlrenderer, x + radius, y + h - 1 - radius, radius, gfx_color)
        
        # Reset Clip
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)


    def _render_vbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        """Render a VBox layout."""
        x, y, w, h = rect
        
        # Render background if color is specified
        if item.get(core.KEY_COLOR):
             # Reuse the primitive drawer, treating this vbox as a rect for background purposes
             # We create a temporary item dict/context or just pass item? 
             # item has 'color', 'radius' etc (via extra in python obj, merged in to_data)
             self._draw_rect_primitive(item, rect)

        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        # Resolve padding
        pt = self._resolve_val(raw_padding[0], h)
        pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h)
        pl = self._resolve_val(raw_padding[3], w)
        padding = (pt, pr, pb, pl)
        
        children = item.get(core.KEY_CHILDREN, [])
        
        # Cursor info
        cursor_x = x + pl
        cursor_y = y + pt
        available_width = w - pr - pl
        available_height = h - pt - pb
        
        for child in children:
            raw_margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0)) # t, r, b, l
            mt = self._resolve_val(raw_margin[0], available_height)
            mr = self._resolve_val(raw_margin[1], available_width)
            mb = self._resolve_val(raw_margin[2], available_height)
            ml = self._resolve_val(raw_margin[3], available_width)
            margin = (mt, mr, mb, ml)
            
            # Resolve child dimensions
            child_raw_rect = child.get(core.KEY_RECT, [0,0,0,0])
            child_w = self._resolve_val(child_raw_rect[2], available_width)
            child_h = self._measure_item(child, child_w, available_height)
            
            child_x = cursor_x + margin[3]
            child_y = cursor_y + margin[0]
            
            child_rect = (child_x, child_y, child_w, child_h)
            
            # CULLING
            if viewport:
                vx, vy, vw, vh = viewport
                # Check intersection (vertical mostly for VBox)
                # If child bottom < viewport top OR child top > viewport bottom
                # child_y is absolute top
                if (child_y + child_h < vy) or (child_y > vy + vh):
                     # Skip Rendering
                     pass
                else:
                     self._render_element_at(child, child_rect, viewport)
            else:
                self._render_element_at(child, child_rect, viewport)
            
            cursor_y += margin[0] + child_h + margin[2]

    def _render_hbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        """Render an HBox layout."""
        x, y, w, h = rect

        # Render background
        if item.get(core.KEY_COLOR):
             self._draw_rect_primitive(item, rect)

        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        # Resolve padding
        pt = self._resolve_val(raw_padding[0], h)
        pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h)
        pl = self._resolve_val(raw_padding[3], w)
        padding = (pt, pr, pb, pl)
        
        children = item.get(core.KEY_CHILDREN, [])
        
        cursor_x = x + padding[3]
        cursor_y = y + padding[0]
        available_width = w - padding[1] - padding[3]
        available_height = h - padding[0] - padding[2]
        
        for child in children:
            raw_margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
            mt = self._resolve_val(raw_margin[0], available_height)
            mr = self._resolve_val(raw_margin[1], available_width)
            mb = self._resolve_val(raw_margin[2], available_height)
            ml = self._resolve_val(raw_margin[3], available_width)
            margin = (mt, mr, mb, ml)
            
            child_raw_rect = child.get(core.KEY_RECT, [0,0,0,0])
            
            # Auto Width support for HBox children
            if child_raw_rect[2] == "auto":
                 child_w = self._measure_item_width(child, available_height)
            else:
                 child_w = self._resolve_val(child_raw_rect[2], available_width)
            
            child_h = self._measure_item(child, child_w, available_height)
            
            child_x = cursor_x + margin[3]
            child_y = cursor_y + margin[0]
            
            child_rect = (child_x, child_y, child_w, child_h)
            
            child_rect = (child_x, child_y, child_w, child_h)
            
            # Culling for HBox (Horizontal)
            if viewport:
                 vx, vy, vw, vh = viewport
                 if (child_x + child_w < vx) or (child_x > vx + vw):
                      pass
                 else:
                      self._render_element_at(child, child_rect, viewport)
            else:
                 self._render_element_at(child, child_rect, viewport)
            
            cursor_x += margin[3] + child_w + margin[1]

    def _render_element_at(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        """Render an element at a specific absolute rectangle."""
        item_type = item.get(core.KEY_TYPE)
        
        if item_type == core.TYPE_VBOX:
            self._render_vbox(item, rect, viewport)
        elif item_type == core.TYPE_HBOX:
            self._render_hbox(item, rect, viewport)
        elif item_type == core.TYPE_RECT:
            color = item.get("color", (255, 255, 255, 255))
            self.renderer.fill(rect, color)
        elif item_type == core.TYPE_TEXT:
            self._render_text(item, rect)
        elif item_type == core.TYPE_IMAGE:
            self._flush_render_queue() # Ensure Z-order
            self._render_image(item, rect)

    def _render_scrollable_layer(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        """Render a Scrollable Layer with clipping."""
        x, y, w, h = rect
        scroll_y = item.get(core.KEY_SCROLL_Y, 0)
        
        # Set Clip Rect to this layer bounds
        # SDL2 expects proper SDL_Rect structure or 4 args? checking pysdl2.
        # pysdl2 renderer.clip = (...) property wrapper does SDL_RenderSetClipRect
        # But we access the raw sdl renderer if needed, or use pysdl2 wrapper property if available?
        # self.renderer is sdl2.ext.Renderer
        # It doesn't seem to expose clip rect easily via high level API in older versions, 
        # but modern pysdl2 might.
        # Let's try direct SDL call to be safe and robust.
        
        clip_rect = sdl2.SDL_Rect(x, y, w, h)
        # Use direct SDL2 function, passing the renderer pointer
        self._flush_render_queue() # Flush before changing clip state
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, clip_rect)
        
        # Children are rendered with dy = -scroll_y
        # Their coordinates are typically relative to this layer (0,0 based?) or absolute logic?
        # In current recursion, we pass 'rect' as parent_rect.
        # If children are positioned relative to parent:
        # standard resolution does: px + child_x.
        # So child absolute X = x + child_x.
        # We need absolute Y = y + child_y - scroll_y.
        
        # We can simulate this by passing a virtual parent rect that is shifted up.
        # virtual_parent_rect = (x, y - scroll_y, w, h)
        # Wait, height/width context for percentages should remain true 'w', 'h'.
        # But position context should be shifted.
        
        # _resolve_rect uses the parent rect for both position base and size context.
        # If we shift Y, size context (h) remains correct.
        
        virtual_parent_rect = (x, y - scroll_y, w, h)
        
        # Define New Viewport (Clip Rect)
        # If an existing viewport existed, we should intersect? 
        # Usually scrollable layer IS the viewport provider.
        current_viewport = (x, y, w, h)

        children = item.get(core.KEY_CHILDREN, [])
        for child in children:
            self._render_item(child, virtual_parent_rect, current_viewport)
            
        # Unset Clip Rect (or pop) - Setting to None disables clipping
        self._flush_render_queue() # Flush inside clipped region before unsetting
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)

    def _render_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        """Render text within a given rect with optional wrapping and ellipsis."""
        self._flush_render_queue() # Textures must be drawn after background rects
        if not hasattr(self, "ttf_available") or not self.ttf_available:
            return

        text = item.get(core.KEY_TEXT, "")
        if not text:
            return
            
        markup = item.get(core.KEY_MARKUP, False)
        if markup:
             self._render_rich_text(item, rect)
             return
             
        # ... (Old plain text logic calls _render_plain_wrapped)
        # Refactoring to keep code clean.
        self._render_plain_text(item, rect, text)

    def _get_font_manager(self, font_path, size, color, bold=False):
        cache_key = f"{font_path}_{size}_{color}_{bold}"
        font_manager = self._font_cache.get(cache_key)
        if not font_manager:
            try:
                font_manager = sdl2.ext.FontManager(font_path, size=size, color=color)
                if bold:
                    if hasattr(font_manager, "font"):
                        sdlttf.TTF_SetFontStyle(font_manager.font, sdlttf.TTF_STYLE_BOLD)
                self._font_cache[cache_key] = font_manager
            except Exception:
                return None
        return font_manager

    def _render_plain_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], text: str) -> None:
        # Extracted plain text logic
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        raw_size = item.get(core.KEY_FONT_SIZE, 16)
        size = self._resolve_val(raw_size, rect[3])
        if size <= 0: size = 1
        color = item.get(core.KEY_COLOR, (0, 0, 0, 255))
        align = item.get(core.KEY_ALIGN, "left")
        do_wrap = item.get(core.KEY_WRAP, True)
        do_ellipsis = item.get(core.KEY_ELLIPSIS, True)
        
        font_manager = self._get_font_manager(font_path, size, color)
        if not font_manager: return

        try:
            def measure(text_str):
                surf = font_manager.render(text_str)
                return surf.w, surf.h

            max_width = rect[2]
            max_height = rect[3]
            lines = []
            
            if not do_wrap:
                lines = [text]
            else:
                words = text.split(" ")
                current_line = []
                for word in words:
                    test_line = " ".join(current_line + [word])
                    w, h = measure(test_line)
                    if w > max_width and current_line:
                         lines.append(" ".join(current_line))
                         current_line = [word]
                    else:
                        current_line.append(word)
                if current_line:
                    lines.append(" ".join(current_line))

            _, single_line_h = measure("Tg")
            total_height = len(lines) * single_line_h
            
            if total_height > max_height and do_ellipsis:
                max_lines = max(1, max_height // single_line_h)
                if len(lines) > max_lines:
                    lines = lines[:max_lines]
                    last_line = lines[-1]
                    while True:
                        w, _ = measure(last_line + "...")
                        if w <= max_width:
                            lines[-1] = last_line + "..."
                            break
                        if len(last_line) == 0: break
                        last_line = last_line[:-1]
            
            current_y = rect[1]
            current_y = rect[1]
            for line in lines:
                # Cache lookup
                # Ensure color is hashable (tuple)
                cache_key = (font_path, size, tuple(color), line)
                texture = self._text_texture_cache.get(cache_key)

                if not texture:
                    surface = font_manager.render(line)
                    if not surface: continue
                    texture = sdl2.ext.Texture(self.renderer, surface)
                    self._text_texture_cache[cache_key] = texture

                # Calculate width/height from texture usually, but we need Surface for w/h?
                # sdl2.ext.Texture has .size property (w, h)
                tw, th = texture.size

                tx = rect[0]
                if align == "center":
                    tx = rect[0] + (rect[2] - tw) // 2
                elif align == "right":
                    tx = rect[0] + rect[2] - tw
                self.renderer.copy(texture, dstrect=(tx, current_y, tw, th))
                current_y += single_line_h
                if current_y > rect[1] + max_height: break

        except Exception:
            return

    def _calculate_rich_text_lines(self, item: Dict[str, Any], max_width: int):
        text = item.get(core.KEY_TEXT, "")
        base_color = item.get(core.KEY_COLOR, (0, 0, 0, 255))
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        
        # Get font size (requires resolving against something? Height usually... 
        # If height is auto, we can't resolve font size against height if it depends on it.
        # But usually font size is absolute or relative to parent height?
        # Let's assume standard resolve_val call has been done or we do it here.
        # We need 'size' resolved.
        # The caller should explicitly resolve font size if needed or we use a fallback context.
        # For 'auto' height, font size cannot optionally depend on self height.
        # We'll use 0 as context for size resolution if needed, or pass it in.
        pass

    def _measure_item(self, item: Dict[str, Any], available_width: int, available_height: int = 0) -> int:
        """Measure the height of an item given the available width."""
        item_type = item.get(core.KEY_TYPE)
        
        # Check Cache
        item_id = item.get(core.KEY_ID)
        if item_id:
             cache_key = (item_id, available_width)
             if cache_key in self._measurement_cache:
                  return self._measurement_cache[cache_key]

        if core.KEY_RECT in item:
            raw_rect = item[core.KEY_RECT]
            raw_height = raw_rect[3]
            
            # If fixed height, resolve and return (unless it is auto)
            # Optimization: If type is specific (like VBox), maybe we still want to re-measure content?
            # Usually strict setting overrides content.
            if raw_height != "auto":
                 h = self._resolve_val(raw_height, available_height)
                 return h
        
        # If auto, measure based on type
        if item_type == core.TYPE_TEXT:
             h = self._measure_text_height(item, available_width, available_height)
             if item_id: self._measurement_cache[cache_key] = h
             return h
             
        elif item_type == core.TYPE_VBOX:
             raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
             pt = self._resolve_val(raw_padding[0], available_height)
             pb = self._resolve_val(raw_padding[2], available_height)
             pl = self._resolve_val(raw_padding[3], available_width)
             pr = self._resolve_val(raw_padding[1], available_width)
             
             total_h = pt + pb
             inner_width = max(0, available_width - pl - pr)
             inner_height = max(0, available_height - pt - pb)
             
             for child in item.get(core.KEY_CHILDREN, []):
                 raw_margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
                 mt = self._resolve_val(raw_margin[0], inner_height)
                 mb = self._resolve_val(raw_margin[2], inner_height)
                 
                 child_w_raw = child.get(core.KEY_RECT, [0,0,100,0])[2]
                 child_w = self._resolve_val(child_w_raw, inner_width)
                 
                 child_h = self._measure_item(child, child_w, inner_height)
                 total_h += mt + child_h + mb
             
             if item_id: self._measurement_cache[cache_key] = total_h
             return total_h

        elif item_type == core.TYPE_HBOX:
             # ... hbox logic ...
             raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
             pt = self._resolve_val(raw_padding[0], available_height)
             pb = self._resolve_val(raw_padding[2], available_height)
             pl = self._resolve_val(raw_padding[3], available_width)
             pr = self._resolve_val(raw_padding[1], available_width)
             
             inner_width = max(0, available_width - pl - pr)
             inner_height = max(0, available_height - pt - pb)
             max_child_h = 0
             
             for child in item.get(core.KEY_CHILDREN, []):
                 raw_margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
                 mt = self._resolve_val(raw_margin[0], inner_height)
                 mb = self._resolve_val(raw_margin[2], inner_height)
                 
                 child_w_raw = child.get(core.KEY_RECT, [0,0,100,0])[2]
                 child_w = self._resolve_val(child_w_raw, inner_width)
                 
                 child_h = self._measure_item(child, child_w, inner_height)
                 max_child_h = max(max_child_h, mt + child_h + mb)
             
             total_h = pt + max_child_h + pb
             if item_id: self._measurement_cache[cache_key] = total_h
             return total_h

        elif item_type == core.TYPE_IMAGE:
             # Check for explicit width
             raw_w = item.get(core.KEY_RECT, [0,0,0,0])[2]
             if raw_w == "auto":
                 target_w = self._measure_item_width(item, 0)
             else:
                 target_w = self._resolve_val(raw_w, available_width)
            
             h = self._measure_image_height(item, target_w)
             if item_id: self._measurement_cache[cache_key] = h
             return h

        # Cache result
        if item_id:
             raw_h = item.get(core.KEY_RECT, [0,0,0,0])[3]
             fallback_h = 0
             if raw_h != "auto":
                 fallback_h = self._resolve_val(raw_h, available_height if available_height > 0 else 0)
             
             self._measurement_cache[cache_key] = fallback_h
             return fallback_h
              
        raw_h = item.get(core.KEY_RECT, [0,0,0,0])[3]
        if raw_h != "auto":
             return self._resolve_val(raw_h, available_height if available_height > 0 else 0)
        
        return 0

    def _measure_item_width(self, item: Dict[str, Any], parent_height: int = 0) -> int:
        """Measure the width of an item."""
        item_type = item.get(core.KEY_TYPE)
        if item_type == core.TYPE_TEXT:
             return self._measure_text_width(item, parent_height)
        
        elif item_type == core.TYPE_HBOX:
            # Measure children
            raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
            # Padding resolution requires knowing parent width usually, but here we are measuring intrinsic width.
            # We can't resolve relative padding easily without context. Assume 0 for strict intrinsic measurement? 
            # Or pass a context? For auto-width, we usually want minimal fit.
            # Let's assume pixel padding or minor dependency.
            # _resolve_val returns 0 if % and no parent_len.
            
            pl = self._resolve_val(raw_padding[3], 0)
            pr = self._resolve_val(raw_padding[1], 0)
            
            total_w = pl + pr
            children = item.get(core.KEY_CHILDREN, [])
            for child in children:
                raw_margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
                ml = self._resolve_val(raw_margin[3], 0)
                mr = self._resolve_val(raw_margin[1], 0)
                
                child_w_raw = child.get(core.KEY_RECT, [0,0,"auto",0])[2]
                
                if child_w_raw == "auto":
                    child_w = self._measure_item_width(child, parent_height)
                else:
                    child_w = self._resolve_val(child_w_raw, 0)
                
                total_w += ml + child_w + mr
            
            return total_w

        # Generic Fallback (Rect, Image, etc)
        # If they have a resolution strategy in _measure_item, we might duplicate logic or simplify
        # For Width, primitive usually has fixed width or % width.
        # If fixed, we resolve it. If %, returns 0 (correct for intrinsic).
        # If "auto", primitives usually don't support auto width unless Text/Image.
        
        raw_w = item.get(core.KEY_RECT, [0,0,0,0])[2]
        if raw_w != "auto":
             return self._resolve_val(raw_w, 0)
             
        # Image auto-width?
        if item_type == core.TYPE_IMAGE:
             # Basic image support: get source texture width
             src = item.get(core.KEY_SOURCE)
             if src:
                 surface = self._load_image_source(src)
                 if surface:
                     return surface.w
             
        return 0
    
    def _measure_text_width(self, item: Dict[str, Any], parent_height: int = 0) -> int:
        text = item.get(core.KEY_TEXT, "")
        if not text: return 0
        
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        raw_size = item.get(core.KEY_FONT_SIZE, 16)
        size = self._resolve_val(raw_size, parent_height) if parent_height > 0 else (raw_size if isinstance(raw_size, int) else 16)
        if size <= 0: size = 16
        base_color = item.get(core.KEY_COLOR, (0, 0, 0, 255))
        
        markup = item.get(core.KEY_MARKUP, False)
        if markup:
             parser = markdown.MarkdownParser(default_color=base_color)
             segments = parser.parse(text)
             total_w = 0
             for seg in segments:
                 fm = self._get_font_manager(font_path, size, seg.color, seg.bold)
                 if fm:
                     surf = fm.render(seg.text) 
                     total_w += surf.w
             return total_w
        else:
             fm = self._get_font_manager(font_path, size, base_color)
             if fm:
                 surf = fm.render(text)
                 return surf.w
        return 0

    def _measure_text_height(self, item: Dict[str, Any], width: int, parent_height: int = 0) -> int:
        """Measure required height for text item."""
        if item.get(core.KEY_MARKUP, False):
            return self._measure_rich_text_height(item, width, parent_height)
        else:
            # Placeholder for plain text measurement
             return 20 # fixed for now or implement plain text measure
    
    def _measure_rich_text_height(self, item: Dict[str, Any], width: int, parent_height: int) -> int:
        text = item.get(core.KEY_TEXT, "")
        base_color = item.get(core.KEY_COLOR, (0, 0, 0, 255))
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        raw_size = item.get(core.KEY_FONT_SIZE, 16)
        
        # Resolve size. if parent_height is 0 (likely for auto logic on VBox root?), we might default to absolute.
        size = self._resolve_val(raw_size, parent_height) if parent_height > 0 else (raw_size if isinstance(raw_size, int) else 16)
        if size <= 0: size = 16

        parser = markdown.MarkdownParser(default_color=base_color)
        segments = parser.parse(text)
        
        chunked_words = []
        for seg in segments:
            lines_in_seg = seg.text.split('\n')
            for i, line_str in enumerate(lines_in_seg):
                words = line_str.split(" ")
                for j, word in enumerate(words):
                    suffix = " " if j < len(words) - 1 else ""
                    chunk = word + suffix
                    if chunk:
                        chunked_words.append((chunk, seg))
                if i < len(lines_in_seg) - 1:
                    chunked_words.append(("\n", seg))
        
        lines = []
        current_line = []
        current_line_width = 0
        
        measure_cache = {}
        def measure_chunk(text_str, seg):
            fm = self._get_font_manager(font_path, size, seg.color, seg.bold)
            if not fm: return 0, 0
            surf = fm.render(text_str)
            return surf.w, surf.h

        _, line_height = measure_chunk("Tg", segments[0] if segments else None) 
        if line_height == 0: line_height = size

        for text_chunk, seg in chunked_words:
            if text_chunk == "\n":
                lines.append(current_line)
                current_line = []
                current_line_width = 0
                continue
                
            w, h = measure_chunk(text_chunk, seg)
            line_height = max(line_height, h)
            
            if current_line and (current_line_width + w > width):
                lines.append(current_line)
                current_line = [(text_chunk, seg, w, h)]
                current_line_width = w
            else:
                current_line.append((text_chunk, seg, w, h))
                current_line_width += w
                
        if current_line:
            lines.append(current_line)
            
        return len(lines) * line_height

    def _render_rich_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        text = item.get(core.KEY_TEXT, "")
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        raw_size = item.get(core.KEY_FONT_SIZE, 16)
        size = self._resolve_val(raw_size, rect[3])
        if size <= 0: size = 1
        base_color = item.get(core.KEY_COLOR, (0, 0, 0, 255))
        do_wrap = item.get(core.KEY_WRAP, True)
        
        # Parse segments
        parser = markdown.MarkdownParser(default_color=base_color)
        segments = parser.parse(text)
        
        chunked_words = []
        for seg in segments:
            lines_in_seg = seg.text.split('\n')
            for i, line_str in enumerate(lines_in_seg):
                words = line_str.split(" ")
                for j, word in enumerate(words):
                    # Re-add space if it wasn't the last word
                    suffix = " " if j < len(words) - 1 else ""
                    chunk = word + suffix
                    if chunk:
                        chunked_words.append((chunk, seg))
                
                # If we had a split (i < len - 1), it means there was a newline
                if i < len(lines_in_seg) - 1:
                    chunked_words.append(("\n", seg))
        
        # Layout lines
        lines = []
        current_line = []
        current_line_width = 0
        max_width = rect[2]
        
        measure_cache = {}
        def measure_chunk(text_str, seg):
            fm = self._get_font_manager(font_path, size, seg.color, seg.bold)
            if not fm: return 0, 0
            surf = fm.render(text_str)
            return surf.w, surf.h

        _, line_height = measure_chunk("Tg", segments[0] if segments else None) 
        if line_height == 0: line_height = size

        for text_chunk, seg in chunked_words:
            if text_chunk == "\n":
                lines.append(current_line)
                current_line = []
                current_line_width = 0
                continue
                
            w, h = measure_chunk(text_chunk, seg)
            line_height = max(line_height, h)
            
            if do_wrap and current_line and (current_line_width + w > max_width):
                lines.append(current_line)
                current_line = [(text_chunk, seg, w, h)]
                current_line_width = w
            else:
                current_line.append((text_chunk, seg, w, h))
                current_line_width += w
                
        if current_line:
            lines.append(current_line)
            
        # Render
        current_y = rect[1]
        start_x = rect[0]
        
        item_align = item.get(core.KEY_ALIGN, "left")

        for line in lines:
            line_x = start_x
            if item_align == "center":
                 # calc line width
                 lw = sum([chunk[2] for chunk in line])
                 line_x = start_x + (max_width - lw) // 2
            
            for text_chunk, seg, w, h in line:
                # Cache Lookup
                cache_key = (font_path, size, tuple(seg.color), text_chunk, seg.bold)
                texture = self._text_texture_cache.get(cache_key)
                
                if not texture:
                    fm = self._get_font_manager(font_path, size, seg.color, seg.bold)
                    if not fm: continue
                
                    surface = fm.render(text_chunk)
                    if not surface: continue
                    texture = sdl2.ext.Texture(self.renderer, surface)
                    self._text_texture_cache[cache_key] = texture
                
                # Render logic
                # We need surface dimensions. Texture has them.
                tw, th = texture.size
                self.renderer.copy(texture, dstrect=(line_x, current_y, tw, th))
                
                # Handle Link Hitbox
                if seg.link_target:
                    chunk_rect = (line_x, current_y, tw, th)
                    self._hit_list.append((chunk_rect, {
                        "type": "link",
                        "target": seg.link_target,
                        core.KEY_LISTEN_EVENTS: [core.EVENT_CLICK]
                    }))
                
                line_x += w
                
            current_y += line_height






    def _render_image(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        """Render an image within the rect."""
        source = item.get(core.KEY_SOURCE)
        if not source:
            return

        scale_mode = item.get(core.KEY_SCALE_MODE, "fit")
        # Try to get existing texture from cache if we have an ID
        # For non-id items, we might warn or just cache by source hash if possible, 
        # but for bytes/callable without ID it's hard to cache efficiently.
        item_id = item.get(core.KEY_ID)
        cache_key = item_id if item_id else str(id(source))
        
        texture = self._image_cache.get(cache_key)
        
        if not texture:
            surface = self._load_image_source(source)
            if surface:
                texture = sdl2.ext.Texture(self.renderer, surface)
                sdl2.SDL_FreeSurface(surface)
                self._image_cache[cache_key] = texture
        
        if not texture:
            return 
            
        # Determine destination rect based on scale_mode
        img_w, img_h = texture.size
        dest_x, dest_y, dest_w, dest_h = rect
        
        final_x, final_y, final_w, final_h = dest_x, dest_y, dest_w, dest_h
        
        if scale_mode == "fit":
             # Scale down to fit within rect maintaining aspect ratio
             if img_w > 0 and img_h > 0:
                 scale = min(dest_w / img_w, dest_h / img_h)
                 final_w = int(img_w * scale)
                 final_h = int(img_h * scale)
                 # Center
                 final_x = dest_x + (dest_w - final_w) // 2
                 final_y = dest_y + (dest_h - final_h) // 2
             
        elif scale_mode == "fill":
             # Stretch to fill
             pass
             
        elif scale_mode == "center":
             final_w = img_w
             final_h = img_h
             final_x = dest_x + (dest_w - img_w) // 2
             final_y = dest_y + (dest_h - img_h) // 2
             
        # Render
        self.renderer.copy(texture, dstrect=(final_x, final_y, final_w, final_h))


    def _load_image_source(self, source: Union[str, bytes, Callable]) -> Any:
        """Load image surface from source."""
        try:
             import sdl2.sdlimage as img
        except ImportError:
             print("SDL_image not available.")
             return None

        surface = None
        
        if isinstance(source, str):
            # File path
            surface = img.IMG_Load(source.encode('utf-8'))
            
        elif isinstance(source, (bytes, bytearray)):
            # Memory
            rw = sdl2.rwops.rw_from_object(source)
            surface = img.IMG_Load_RW(rw, 0)
            
        elif callable(source):
            # Procedural
            res = source()
            if isinstance(res, sdl2.SDL_Surface):
                 surface = res
            elif hasattr(res, "contents") and isinstance(res.contents, sdl2.SDL_Surface):
                 surface = res
            elif isinstance(res, (bytes, bytearray)):
                 return self._load_image_source(res)
        
        return surface
    def _measure_image_height(self, item: Dict[str, Any], width: int) -> int:
        source = item.get(core.KEY_SOURCE)
        if not source: return 0
        id_key = item.get(core.KEY_ID)
        cache_key = id_key if id_key else str(id(source))
        
        texture = self._image_cache.get(cache_key)
        if not texture:
             surface = self._load_image_source(source)
             if surface:
                 texture = sdl2.ext.Texture(self.renderer, surface)
                 sdl2.SDL_FreeSurface(surface)
                 self._image_cache[cache_key] = texture
        
        if not texture: return 0
        
        img_w, img_h = texture.size
        # Calculate height preserving aspect ratio
        if img_w == 0: return 0
        scale = width / img_w
        return int(img_h * scale)
    
    def _measure_image_width(self, item: Dict[str, Any], height: int) -> int:
        source = item.get(core.KEY_SOURCE)
        if not source: return 0
        id_key = item.get(core.KEY_ID)
        cache_key = id_key if id_key else str(id(source))
        
        texture = self._image_cache.get(cache_key)
        if not texture:
             surface = self._load_image_source(source)
             if surface:
                 texture = sdl2.ext.Texture(self.renderer, surface)
                 sdl2.SDL_FreeSurface(surface)
                 self._image_cache[cache_key] = texture
        
        if not texture: return 0
        
        img_w, img_h = texture.size
        if img_h == 0: return 0
        scale = height / img_h
        return int(img_w * scale)
