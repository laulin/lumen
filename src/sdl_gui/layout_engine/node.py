from typing import List, Tuple, Optional
from sdl_gui.layout_engine.definitions import FlexDirection, JustifyContent, AlignItems, FlexWrap
from sdl_gui.layout_engine.style import FlexStyle

class FlexNode:
    def __init__(self, style: FlexStyle = None):
        self.style = style or FlexStyle()
        self.children: List['FlexNode'] = []
        # Absolute layout rect (x, y, w, h)
        self.layout_rect: Tuple[int, int, int, int] = (0, 0, 0, 0)
    
    def add_child(self, child: 'FlexNode'):
        self.children.append(child)

    def calculate_layout(self, available_width: int, available_height: int, x_offset: int = 0, y_offset: int = 0, force_size: bool = False):
        # 1. Resolve own size
        if force_size:
            w = available_width
            h = available_height
        else:
            w = self._resolve_dimension(self.style.width, available_width)
            h = self._resolve_dimension(self.style.height, available_height)
        
        # If width/height not set, they might be determined by children or parent constraint
        # For simplify, assume root node has explicit size or fills availability
        if w is None: w = available_width
        if h is None: h = available_height

        self.layout_rect = (x_offset, y_offset, w, h)
        
        if not self.children:
            return

        # 2. Main Axis & Cross Axis Setup
        is_row = self.style.direction in (FlexDirection.ROW, FlexDirection.ROW_REVERSE)
        main_size = w if is_row else h
        cross_size = h if is_row else w
        
        # 3. First Pass: Measure fixed children and determine free space
        total_main_used = 0
        total_flex_grow = 0
        total_flex_shrink = 0
        
        for child in self.children:
            # Recursive pre-calc if needed? 
            # Ideally we need to know child's basis.
            basis = self._get_flex_basis(child, main_size)
            total_main_used += basis
            total_flex_grow += child.style.grow
            total_flex_shrink += child.style.shrink
        
        # 4. Resolve flexible lengths
        remaining_space = main_size - total_main_used
        
        # 5. Distribute space
        child_main_sizes = []
        for i, child in enumerate(self.children):
            basis = self._get_flex_basis(child, main_size)
            if remaining_space > 0 and total_flex_grow > 0:
                # Grow
                if child.style.grow > 0:
                    extra = remaining_space * (child.style.grow / total_flex_grow)
                    child_main_sizes.append(basis + extra)
                else:
                    child_main_sizes.append(basis)
            elif remaining_space < 0 and total_flex_shrink > 0:
                # Shrink
                # Standard formula is more complex, simplified here:
                shrinkage = abs(remaining_space) * (child.style.shrink / total_flex_shrink)
                child_main_sizes.append(max(0, basis - shrinkage))
            else:
                child_main_sizes.append(basis)

        # 6. Cross Axis Sizing (Stretch or fixed)
        child_cross_sizes = []
        for child in self.children:
            cross_dim_req = child.style.height if is_row else child.style.width
            if cross_dim_req is not None and cross_dim_req != "auto":
                 resolved = self._resolve_dimension(cross_dim_req, cross_size)
                 child_cross_sizes.append(resolved)
            elif self.style.align_items == AlignItems.STRETCH:
                 child_cross_sizes.append(cross_size)
            else:
                 # Auto / content size - for now default to 0 or some content measurement?
                 # In this simplified engine, if no content and no size, it's 0.
                 child_cross_sizes.append(0)

        # 7. Main Axis Positioning (Justify Content)
        # Recalculate used space after flexibility
        final_total_main = sum(child_main_sizes)
        free_space = main_size - final_total_main
        
        start_pos = 0
        gap = 0
        
        if self.style.justify_content == JustifyContent.CENTER:
            start_pos = free_space / 2
        elif self.style.justify_content == JustifyContent.FLEX_END:
            start_pos = free_space
        elif self.style.justify_content == JustifyContent.SPACE_BETWEEN:
            if len(self.children) > 1:
                gap = free_space / (len(self.children) - 1)
        elif self.style.justify_content == JustifyContent.SPACE_AROUND:
             if len(self.children) > 0:
                half_gap = free_space / (len(self.children) * 2)
                start_pos = half_gap
                gap = half_gap * 2
        elif self.style.justify_content == JustifyContent.SPACE_EVENLY:
             if len(self.children) > 0:
                 gap = free_space / (len(self.children) + 1)
                 start_pos = gap
        
        current_main = start_pos
        
        # 8. Final Layout Pass for Children
        for i, child in enumerate(self.children):
            c_main = child_main_sizes[i]
            c_cross = child_cross_sizes[i]
            
            # Cross Axis Positioning (Align Items)
            cross_pos = 0
            if self.style.align_items == AlignItems.CENTER:
                cross_pos = (cross_size - c_cross) / 2
            elif self.style.align_items == AlignItems.FLEX_END:
                cross_pos = cross_size - c_cross
            
            cx, cy, cw, ch = 0, 0, 0, 0
            
            if is_row:
                cx = x_offset + current_main
                cy = y_offset + cross_pos
                cw = c_main
                ch = c_cross
                current_main += c_main + gap
            else:
                cx = x_offset + cross_pos
                cy = y_offset + current_main
                cw = c_cross
                ch = c_main
                current_main += c_main + gap
                
            # Recursively layout child
            child.calculate_layout(cw, ch, cx, cy, force_size=True)


    def _resolve_dimension(self, val, available):
        if val is None: return None
        if val == "auto": return None
        if isinstance(val, int): return val
        if isinstance(val, str) and val.endswith("%"):
            try:
                return float(val[:-1]) / 100.0 * available
            except:
                return 0
        return 0

    def _get_flex_basis(self, child, main_size):
        # Resolve basis
        basis = child.style.basis
        if basis == "auto":
            # If auto, look at width/height
            if self.style.direction in (FlexDirection.ROW, FlexDirection.ROW_REVERSE):
                req = child.style.width
            else:
                req = child.style.height
            
            if req is None: return 0 # Content size not supported yet
            return self._resolve_dimension(req, main_size) or 0
        
        return self._resolve_dimension(basis, main_size)
