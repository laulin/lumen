from typing import List, Tuple, Optional, Union
from sdl_gui.layout_engine.definitions import FlexDirection, JustifyContent, AlignItems, FlexWrap
from sdl_gui.layout_engine.style import FlexStyle

class FlexNode:
    def __init__(self, style: FlexStyle = None):
        self.style = style or FlexStyle()
        self.children: List['FlexNode'] = []
        self.measure_func = None
        self.layout_rect: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self.parent: 'FlexNode' = None
    
    def add_child(self, child: 'FlexNode'):
        self.children.append(child)
        child.parent = self

    def measure(self, available_width: int, available_height: int) -> Tuple[int, int]:
        w = self._resolve_dimension(self.style.width, available_width)
        h = self._resolve_dimension(self.style.height, available_height)
        if w is not None and h is not None: return int(w), int(h)
        if not self.children:
             if self.measure_func: return self._measure_leaf(w, h, available_width, available_height)
             return int(w or 0), int(h or 0)
        old_rect = self.layout_rect
        self.calculate_layout(available_width, available_height, 0, 0, force_size=False)
        _, _, final_w, final_h = self.layout_rect
        self.layout_rect = old_rect
        return int(final_w), int(final_h)

    def _measure_leaf(self, w, h, available_width, available_height):
        mw, mh = self.measure_func(available_width, available_height)
        p = self.style.padding
        return int((w if w is not None else mw) + p[3] + p[1]), int((h if h is not None else mh) + p[0] + p[2])

    def calculate_layout(self, available_width: int, available_height: int, x_offset: int = 0, y_offset: int = 0, force_size: bool = False):
        if force_size: w, h = available_width, available_height
        else: w, h = self._resolve_dimension(self.style.width, available_width), self._resolve_dimension(self.style.height, available_height)
        is_row = self.style.direction in (FlexDirection.ROW, FlexDirection.ROW_REVERSE)
        main_auto, cross_auto = (is_row and w is None) or (not is_row and h is None), (is_row and h is None) or (not is_row and w is None)
        calc_w, calc_h = w if w is not None else available_width, h if h is not None else available_height
        if not self.children:
             final_w = w if force_size else None
             final_h = h if force_size else None
             if final_w is not None and final_h is not None:
                 self.layout_rect = (int(x_offset), int(y_offset), int(final_w), int(final_h))
                 import logging
                 parent_str = f"P:{self.parent.style.direction.value}" if self.parent else "ROOT"
                 logging.debug(f"Leaf layout: rect={self.layout_rect} {parent_str} force={force_size}")
             else:
                 bw, bh = self.measure(available_width, available_height)
                 self.layout_rect = (int(x_offset), int(y_offset), int(bw), int(bh))
             return
        p = self.style.padding
        inner_w, inner_h = max(0, calc_w - p[3] - p[1]), max(0, calc_h - p[0] - p[2])
        main_cap, cross_cap = (inner_w if is_row else inner_h), (inner_h if is_row else inner_w)
        child_main, child_cross, total_main, grow_sum, shrink_sum = self._prepare_children(main_cap, cross_cap, is_row)
        child_main = self._resolve_flex(child_main, main_cap, total_main, grow_sum, shrink_sum, main_auto)
        final_child_cross, max_cross = self._resolve_cross(child_cross, cross_cap, cross_auto, is_row)
        if main_auto: main_cap = self._calc_auto_main(child_main, is_row)
        if cross_auto: cross_cap = max_cross
        self.layout_rect = (int(x_offset), int(y_offset), int((main_cap if is_row else cross_cap) + p[3] + p[1]), int((cross_cap if is_row else main_cap) + p[0] + p[2]))
        self._set_positions(x_offset + p[3], y_offset + p[0], main_cap, cross_cap, child_main, final_child_cross, is_row)

    def _prepare_children(self, main_cap, cross_cap, is_row):
        cm, cc, tm, gs, ss = [], [], 0, 0, 0
        tm += self.style.gap * (len(self.children) - 1) if len(self.children) > 1 else 0
        for child in self.children:
            basis = self._get_flex_basis(child, main_cap, cross_cap)
            m = child.style.margin; m_main = m[3] + m[1] if is_row else m[0] + m[2]
            av_w, av_h = (main_cap, cross_cap) if is_row else (cross_cap, main_cap)
            cw, ch = child.measure(av_w, av_h)
            cm.append(basis); cc.append(ch if is_row else cw)
            tm += basis + m_main; gs += child.style.grow; ss += child.style.shrink
        return cm, cc, tm, gs, ss

    def _resolve_flex(self, child_main, main_cap, total_main, grow_sum, shrink_sum, main_is_auto):
        rem = main_cap - total_main
        if main_is_auto or rem == 0: return child_main
        for i, child in enumerate(self.children):
            if rem > 0 and grow_sum > 0 and child.style.grow > 0: child_main[i] += rem * (child.style.grow / grow_sum)
            elif rem < 0 and shrink_sum > 0 and child.style.shrink > 0: child_main[i] = max(0, child_main[i] - abs(rem) * (child.style.shrink / shrink_sum))
        return child_main

    def _resolve_cross(self, child_cross, cross_cap, cross_is_auto, is_row):
        final, max_c = [], 0
        for i, child in enumerate(self.children):
            m = child.style.margin; m_cross = m[0] + m[2] if is_row else m[3] + m[1]
            c_cross = child_cross[i]
            req = child.style.height if is_row else child.style.width
            if req is not None and req != "auto" and not (isinstance(req, (int, float)) and req == 0): c_cross = self._resolve_dimension(req, cross_cap)
            elif self.style.align_items == AlignItems.STRETCH and not cross_is_auto: 
                c_cross = cross_cap - m_cross
                import logging
                logging.debug(f"STRETCH TRIGGERED: c_cross={c_cross} cross_cap={cross_cap}")
            final.append(c_cross); max_c = max(max_c, c_cross + m_cross)
        return final, max_c

    def _calc_auto_main(self, child_main, is_row):
        main = sum(child_main) + (self.style.gap * (len(self.children) - 1) if len(self.children) > 1 else 0)
        for child in self.children:
             m = child.style.margin; main += (m[3] + m[1] if is_row else m[0] + m[2])
        return main

    def _set_positions(self, ctx_x, ctx_y, main_cap, cross_cap, child_main, final_cross, is_row):
        tm_with_m = sum(child_main) + (self.style.gap * (len(self.children) - 1) if len(self.children) > 1 else 0)
        for c in self.children: m = c.style.margin; tm_with_m += (m[3] + m[1] if is_row else m[0] + m[2])
        free = main_cap - tm_with_m
        start, gap = self._get_justify_params(free)
        curr_m = start
        for i, child in enumerate(self.children):
            m = child.style.margin; c_m, c_c = child_main[i], final_cross[i]
            ms, me = (m[3], m[1]) if is_row else (m[0], m[2])
            cs = self._get_align_pos(child, cross_cap, c_c, is_row)
            if is_row: cx, cy, cw, ch = ctx_x + curr_m + ms, ctx_y + cs, c_m, c_c
            else: cx, cy, cw, ch = ctx_x + cs, ctx_y + curr_m + ms, c_c, c_m
            child.calculate_layout(cw, ch, cx, cy, force_size=True)
            curr_m += (c_m + ms + me) + gap

    def _get_justify_params(self, free):
        start, gap = 0, self.style.gap
        jc = self.style.justify_content
        if jc == JustifyContent.CENTER: start = free / 2
        elif jc == JustifyContent.FLEX_END: start = free
        elif jc == JustifyContent.SPACE_BETWEEN and len(self.children) > 1: gap = free / (len(self.children) - 1) + gap
        elif jc == JustifyContent.SPACE_AROUND and len(self.children) > 0: unit = free / (len(self.children) * 2); start, gap = unit, unit * 2 + gap
        elif jc == JustifyContent.SPACE_EVENLY and len(self.children) > 0: gap = free / (len(self.children) + 1) + gap; start = free / (len(self.children) + 1)
        return start, gap

    def _get_align_pos(self, child, cross_cap, c_c, is_row):
        m = child.style.margin; ms, me = (m[0], m[2]) if is_row else (m[3], m[1])
        if self.style.align_items == AlignItems.CENTER: return (cross_cap - (c_c + ms + me)) / 2 + ms
        if self.style.align_items == AlignItems.FLEX_END: return cross_cap - c_c - me
        return ms

    def _resolve_dimension(self, val, available):
        if val is None or val == "auto": return None
        if isinstance(val, (int, float)): return val
        if isinstance(val, str) and val.endswith("%"):
            try: return float(val[:-1]) / 100.0 * available
            except: return 0
        return 0

    def _get_flex_basis(self, child, main_cap, cross_cap):
        basis = child.style.basis
        if basis == "auto":
            is_row = self.style.direction in (FlexDirection.ROW, FlexDirection.ROW_REVERSE)
            req = child.style.width if is_row else child.style.height
            if req is not None and req != "auto": return self._resolve_dimension(req, main_cap) or 0
            av_w, av_h = (main_cap, cross_cap) if is_row else (cross_cap, main_cap)
            cw, ch = child.measure(av_w, av_h)
            return cw if is_row else ch
        return self._resolve_dimension(basis, main_cap) or 0
