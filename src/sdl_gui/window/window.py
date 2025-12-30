import sdl2
import sdl2.ext
from typing import List, Dict, Any, Tuple, Union
from sdl_gui import core


class Window:
    """SDL Window wrapper that renders a display list."""
    
    def __init__(self, title: str, width: int, height: int):
        sdl2.ext.init()
        self.window = sdl2.ext.Window(title, size=(width, height), flags=sdl2.SDL_WINDOW_RESIZABLE)
        self.renderer = sdl2.ext.Renderer(self.window)
        
        # Hit list for event handling (list of tuples: (rect, item_data))
        self._hit_list: List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]] = []

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

    def dispatch_events(self, events: List[Any]) -> None:
        """Dispatch SDL events to primitives."""
        # Process events
        for event in events:
            # Handle Click
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                mx, my = event.button.x, event.button.y
                self._handle_click(mx, my)

            # Handle Hover/Motion if needed (not implemented in this step explicitly but structure is here)

    def _handle_click(self, mx: int, my: int) -> None:
        """Handle click event by checking hit list in reverse order."""
        # Iterate in reverse to find top-most element first
        for rect, item in reversed(self._hit_list):
            x, y, w, h = rect
            if x <= mx < x + w and y <= my < y + h:
                # HIT!
                item_events = item.get(core.KEY_EVENTS, {})
                on_click = item_events.get(core.EVENT_CLICK)
                if on_click:
                    on_click()
                    return # Stop propagation? For now, yes, consume event.

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

    def _render_vbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        """Render a VBox layout."""
        x, y, w, h = rect
        padding = item.get(core.KEY_PADDING, (0, 0, 0, 0)) # top, right, bottom, left
        children = item.get(core.KEY_CHILDREN, [])
        
        # Cursor info
        cursor_x = x + padding[3] # left
        cursor_y = y + padding[0] # top
        available_width = w - padding[1] - padding[3] # w - right - left
        available_height = h - padding[0] - padding[2] # h - top - bottom
        
        for child in children:
            margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0)) # t, r, b, l
            
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
            # note: we pass child_rect as parent_rect, but for primitives without children it acts as their rect
            # Wait, for primitives, _render_item resolves again. 
            # We need to bypass re-resolution of X/Y if we enforce layout.
            # But the recursive `_render_item` logic uses `_resolve_rect` which adds X/Y.
            # If we pass `child_rect` as parent to `_render_item`, and child has `x=0, y=0`, it works.
            # But if child has `x=10`, it adds 10. 
            # Layouts usually ignore child position props, or treat them as offsets.
            # Let's handle it by passing the resolved rect as the context, assuming child x/y are 0 or offsets.
            
            # Better approach: We need to override the child's resolved rect.
            # `_render_item` logic fundamentally assumes relative resolution.
            # If we call `_render_item(child, child_rect)`, it will resolve child's x/y against child_rect... 
            # which is wrong. It resolves against PARENT rect.
            
            # To fix this, we need `_render_item` to accept an override or we construct a "virtual parent"
            # such that the resolution yields `child_rect`.
            
            # Actually, standard behavior: Child X/Y in VBox should probably be ignored or treated as offset.
            # Let's say we pass `rect` (VBox bounds) as parent, but we modify the child's data on the fly? No, mutation bad.
            
            # Let's split rendering logic. `_render_item` is for "flow" or "absolute relative".
            # `_render_vbox` manually calculates positions.
            
            # If I call `self._render_item(child, ...)` it will trigger standard resolution.
            # We want to Enforce the calculated rect.
            
            # Hack/Solution: Pass the calculated global rect and let render item handle it?
            # Creating a dedicated method `_render_child_at(child, abs_rect)` might be cleaner.
            
            self._render_element_at(child, child_rect)
            
            # Advance cursor
            cursor_y += margin[0] + child_h + margin[2]

    def _render_hbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:
        """Render an HBox layout."""
        x, y, w, h = rect
        padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        children = item.get(core.KEY_CHILDREN, [])
        
        cursor_x = x + padding[3]
        cursor_y = y + padding[0]
        available_width = w - padding[1] - padding[3]
        available_height = h - padding[0] - padding[2]
        
        for child in children:
            margin = child.get(core.KEY_MARGIN, (0, 0, 0, 0))
            
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
        # Handle recursive layers? Usually layout items aren't layers, but if they are...
        # For this scope, let's assume primitives or nested layouts.


