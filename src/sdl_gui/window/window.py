import sdl2
import sdl2.ext
from typing import List, Dict, Any, Tuple, Union
from sdl_gui import core


class Window:
    """SDL Window wrapper that renders a display list."""
    
    def __init__(self, title: str, width: int, height: int):
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
        self.renderer = sdl2.ext.Renderer(self.window)
        
        # Hit list for event handling (list of tuples: (rect, item_data))
        self._hit_list: List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]] = []
        
        # Font cache: key -> FontManager
        self._font_cache: Dict[str, sdl2.ext.FontManager] = {}

        self.width = width
        self.height = height
        
    def show(self) -> None:
        """Show the window."""
        self.window.show()

    def render(self, display_list: List[Dict[str, Any]]) -> None:
        """Render the display list."""
        self.renderer.clear()
        
        # Determine current window size (in case of resize)
        # Use dynamic size from SDL window
        width, height = self.window.size
        
        # Sync logical size to avoid scaling artifacts
        self.renderer.logical_size = (width, height)
        
        root_rect = (0, 0, width, height)

        # Clear hit list for this frame
        self._hit_list = []

        for item in display_list:
            self._render_item(item, root_rect)
            
        self.renderer.present()

    def get_ui_events(self) -> List[Dict[str, Any]]:
        """
        Process SDL events and translate them into UI events based on hit tests.
        Returns a list of high-level UI events (e.g. {'type': 'click', 'target': 'id'}).
        """
        sdl_events = sdl2.ext.get_events()
        ui_events = []
        
        for event in sdl_events:
            # Handle Click
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                mx, my = event.button.x, event.button.y
                # Pass the event type we are looking for (CLICK)
                clicked_item = self._find_hit(mx, my, core.EVENT_CLICK)
                
                if clicked_item:
                    item_id = clicked_item.get(core.KEY_ID)
                    # We already know it listens to CLICK because _find_hit filtered it
                    
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



    def _resolve_val(self, val: Union[int, str], parent_len: int) -> int:
        """Resolve a value (int or percentage string) to pixels."""
        if isinstance(val, int):
            return val
        elif isinstance(val, str) and val.endswith("%"):
            try:
                pct = float(val[:-1])
                return int(parent_len * (pct / 100))
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


    def _render_item(self, item: Dict[str, Any], parent_rect: Tuple[int, int, int, int]) -> None:
        """Render a single item recursively."""

        # Resolve current item's rect
        # For Root/Layer items, we resolve against parent.
        # However, for children of VBox/HBox, the position will be overridden by the layout algorithm.
        # But here we handle generic resolution.
        
        raw_rect = item.get(core.KEY_RECT)
        current_rect = parent_rect
        
        if raw_rect:
            current_rect = self._resolve_rect(raw_rect, parent_rect)

        # CAPTURE HIT (Register this item for event handling)
        # We store the resolved absolute rect and the item data
        self._hit_list.append((current_rect, item))

        item_type = item.get(core.KEY_TYPE)
        
        if item_type == core.TYPE_LAYER:
            children = item.get(core.KEY_CHILDREN, [])
            for child in children:
                self._render_item(child, current_rect)

        elif item_type == core.TYPE_VBOX:
            self._render_vbox(item, current_rect)

        elif item_type == core.TYPE_HBOX:
            self._render_hbox(item, current_rect)

        elif item_type == core.TYPE_RECT:
            color = item.get("color", (255, 255, 255, 255))
            if raw_rect: # Only draw if it has a rect
                self.renderer.fill(current_rect, color)
        
        elif item_type == core.TYPE_TEXT:
            self._render_text(item, current_rect)

    def _render_vbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        """Render a VBox layout."""
        x, y, w, h = rect
        raw_padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        # Resolve padding
        pt = self._resolve_val(raw_padding[0], h)
        pr = self._resolve_val(raw_padding[1], w)
        pb = self._resolve_val(raw_padding[2], h)
        pl = self._resolve_val(raw_padding[3], w)
        padding = (pt, pr, pb, pl)
        
        children = item.get(core.KEY_CHILDREN, [])
        
        # Cursor info
        cursor_x = x + pl # left
        cursor_y = y + pt # top
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
            # Width/Height are resolved against available space in VBox
            child_raw_rect = child.get(core.KEY_RECT, [0,0,0,0])
            
            # Resolve size (indices 2 and 3)
            child_w = self._resolve_val(child_raw_rect[2], available_width)
            child_h = self._resolve_val(child_raw_rect[3], available_height)
            
            # Position is determined by cursor + margin
            child_x = cursor_x + margin[3]
            child_y = cursor_y + margin[0]
            
            # Construct resolved rect for child
            child_rect = (child_x, child_y, child_w, child_h)
            
            # Render child
            self._render_element_at(child, child_rect)
            
            # Advance cursor
            cursor_y += margin[0] + child_h + margin[2]

    def _render_hbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        """Render an HBox layout."""
        x, y, w, h = rect
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
            child_w = self._resolve_val(child_raw_rect[2], available_width)
            child_h = self._resolve_val(child_raw_rect[3], available_height)
            
            child_x = cursor_x + margin[3]
            child_y = cursor_y + margin[0]
            
            child_rect = (child_x, child_y, child_w, child_h)
            
            self._render_element_at(child, child_rect)
            
            cursor_x += margin[3] + child_w + margin[1]

    def _render_element_at(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        """Render an element at a specific absolute rectangle."""
        item_type = item.get(core.KEY_TYPE)
        
        if item_type == core.TYPE_VBOX:
            self._render_vbox(item, rect)
        elif item_type == core.TYPE_HBOX:
            self._render_hbox(item, rect)
        elif item_type == core.TYPE_RECT:
            color = item.get("color", (255, 255, 255, 255))
            self.renderer.fill(rect, color)
        elif item_type == core.TYPE_TEXT:
            self._render_text(item, rect)

    def _render_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        """Render text within a given rect with optional wrapping and ellipsis."""
        if not hasattr(self, "ttf_available") or not self.ttf_available:
            return

        text = item.get(core.KEY_TEXT, "")
        if not text:
            return
            
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        
        # Resolve size relative to element height
        raw_size = item.get(core.KEY_FONT_SIZE, 16)
        size = self._resolve_val(raw_size, rect[3])
        if size <= 0:
            size = 1
            
        color = item.get(core.KEY_COLOR, (0, 0, 0, 255))
        align = item.get(core.KEY_ALIGN, "left")
        do_wrap = item.get(core.KEY_WRAP, True)
        do_ellipsis = item.get(core.KEY_ELLIPSIS, True)
        
        cache_key = f"{font_path}_{size}_{color}"
        
        font_manager = self._font_cache.get(cache_key)
        if not font_manager:
            try:
                # Need to initialize ttf if not already? FontManager does it?
                # FontManager(font_path, size=16, color=WHITE, bg_color=BLACK)
                font_manager = sdl2.ext.FontManager(font_path, size=size, color=color)
                self._font_cache[cache_key] = font_manager
            except Exception as e:
                # print(f"Failed to load font {font_path}: {e}")
                return

        try:
             # Basic rendering if no wrap needed or single line fits
            # But checking fits requires measurement.
            
            # Helper to measure text
            def measure(text_str):
                # Using size=size (already set in manager)
                # render returns surface, we can check w
                # This is a bit heavy, invoking render to measure. 
                # SDL_ttf has SizeText, but FontManager hides it mostly?
                # We can access font object?
                # For simplicity, we assume we render to measure if no direct access.
                # Actually FontManager.render(text) returns surface.
                surf = font_manager.render(text_str)
                return surf.w, surf.h

            max_width = rect[2]
            max_height = rect[3]
            
            lines = []
            
            if not do_wrap:
                lines = [text]
            else:
                # Wrapping logic
                words = text.split(" ")
                current_line = []
                
                # Check metrics once
                _, line_height = measure("Tg") # Approximation of line height
                
                # This is a naive word wrapper which calls render many times. 
                # In performance critical code, use TTF_SizeText directly.
                
                for word in words:
                    test_line = " ".join(current_line + [word])
                    w, h = measure(test_line)
                    if w > max_width and current_line:
                        # Line full, push current_line
                         lines.append(" ".join(current_line))
                         current_line = [word]
                    else:
                        current_line.append(word)
                if current_line:
                    lines.append(" ".join(current_line))

            # Ellipsis logic
            # Check total height
            _, single_line_h = measure("Tg")
            total_height = len(lines) * single_line_h
            
            if total_height > max_height and do_ellipsis:
                # How many lines fit?
                max_lines = max(1, max_height // single_line_h)
                if len(lines) > max_lines:
                    lines = lines[:max_lines]
                    # Truncate last line with ...
                    # Iteratively remove chars until it fits
                    last_line = lines[-1]
                    while True:
                        w, _ = measure(last_line + "...")
                        if w <= max_width:
                            lines[-1] = last_line + "..."
                            break
                        if len(last_line) == 0:
                            break
                        last_line = last_line[:-1]
            
            # Render lines
            current_y = rect[1]
            
            # Vertical alignment (if single line or block fits?)
            # Usually text flow starts top-left.
            # If we want vertical centering for the whole block:
            block_height = len(lines) * single_line_h
            if block_height < max_height:
                 # Standard vertical centering
                 # But VBox usually layouting top-down. 
                 # Let's stick to top align for now inside the rect, usually desirable for text flow.
                 # If user wants center, they align the rect itself? 
                 # But our align property is horizontal.
                 # Let's keep top alignment inside the allocated rect.
                 pass

            for line in lines:
                surface = font_manager.render(line)
                if not surface:
                    continue
                texture = sdl2.ext.Texture(self.renderer, surface)
                
                # Align line horizontally
                tx = rect[0]
                if align == "center":
                    tx = rect[0] + (rect[2] - surface.w) // 2
                elif align == "right":
                    tx = rect[0] + rect[2] - surface.w
                
                self.renderer.copy(texture, dstrect=(tx, current_y, surface.w, surface.h))
                current_y += single_line_h
                
                if current_y > rect[1] + max_height:
                    break

        except Exception:
            return
        # Handle recursive layers? Usually layout items aren't layers, but if they are...
        # For this scope, let's assume primitives or nested layouts.


