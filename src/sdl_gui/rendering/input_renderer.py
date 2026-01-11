
import time
from typing import Any, Dict, Tuple

import sdl2
import sdl2.ext

from sdl_gui import core, utils
from sdl_gui.rendering.primitive_renderer import PrimitiveRenderer
from sdl_gui.rendering.text_renderer import TextRenderer


class InputRenderer:
    """
    Handles rendering of Input text fields.
    """

    def __init__(self, primitive_renderer: PrimitiveRenderer, text_renderer: TextRenderer):
        self.primitive_renderer = primitive_renderer
        self.text_renderer = text_renderer
        self._cursor_blink_rate = 0.5
        # Cache for input state to avoid re-rendering unchanged inputs
        self._input_state_cache: Dict[str, Tuple[Any, ...]] = {}

    def _get_input_state_key(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> Tuple:
        """Generate a cache key based on input state that affects rendering."""
        # Cursor blink state affects rendering
        cursor_blink = int(time.time() / self._cursor_blink_rate) % 2
        return (
            item.get("id"),
            item.get(core.KEY_TEXT, ""),
            item.get("cursor_pos", 0),
            item.get("selection_start"),
            item.get("focused", False),
            item.get("scroll_x", 0),
            item.get("scroll_y", 0),
            cursor_blink if item.get("focused") else 0,
            rect,
        )

    def render_input(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> None:

        x, y, w, h = rect

        # --- 1. Background ---
        bg_color = item.get("background_color", (255, 255, 255, 255))
        
        # Only draw background if we have a valid color (and not None)
        if bg_color:
            bg_item = item.copy()
            bg_item[core.KEY_COLOR] = bg_color
            self.primitive_renderer.draw_rect_primitive(bg_item, rect)

        # --- 2. Setup For Text & Cursor ---
        padding = item.get(core.KEY_PADDING, (0, 0, 0, 0))
        pl = utils.resolve_val(padding[3], w)
        pt = utils.resolve_val(padding[0], h)
        pr = utils.resolve_val(padding[1], w)
        pb = utils.resolve_val(padding[2], h)

        content_x = x + pl
        content_y = y + pt
        content_w = max(0, w - pl - pr)
        content_h = max(0, h - pt - pb)

        text = item.get(core.KEY_TEXT, "")
        placeholder = item.get("placeholder", "")
        
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font_size = item.get(core.KEY_FONT_SIZE, 16)
        text_color = item.get(core.KEY_COLOR, (0, 0, 0, 255))

        # Check for placeholder condition
        show_placeholder = (not text) and (not item.get("focused")) and placeholder
        
        display_text = text
        display_color = text_color
        
        if show_placeholder:
            display_text = placeholder
            display_color = (150, 150, 150, 255)

        # Scrolling
        scroll_x = item.get("scroll_x", 0)
        scroll_y = item.get("scroll_y", 0)

        # Clip Logic
        clip_rect = sdl2.SDL_Rect(content_x, content_y, content_w, content_h)
        self.primitive_renderer.flush()
        
        prev_clip = sdl2.SDL_Rect()
        sdl2.SDL_RenderGetClipRect(self.primitive_renderer.renderer.sdlrenderer, ctypes.byref(prev_clip))
        sdl2.SDL_RenderSetClipRect(self.primitive_renderer.renderer.sdlrenderer, clip_rect)

        # --- 3. Render Text Lines ---
        lines = display_text.split('\n')
        line_height = font_size + 4 
        
        start_y = content_y - scroll_y
        start_x = content_x - scroll_x

        current_y = start_y
        
        # Selection logic setup
        sel_start = item.get("selection_start")
        sel_end = item.get("cursor_pos", 0)
        
        has_selection = (sel_start is not None) and (text != "") and (not show_placeholder)
        s_min, s_max = 0, 0
        if has_selection:
             s_min = min(sel_start, sel_end)
             s_max = max(sel_start, sel_end)

        char_idx = 0
        
        for i, line_str in enumerate(lines):
            # Viewport culling
            if current_y + line_height < content_y:
                char_idx += len(line_str) + 1
                current_y += line_height
                continue
            if current_y > content_y + content_h:
                break
                
            # Render Selection
            if has_selection:
                l_start = char_idx
                l_end = char_idx + len(line_str)
                sect_start = max(l_start, s_min)
                sect_end = min(l_end + 1, s_max)
                
                if sect_start < sect_end:
                     # Calculate selection rect
                     t_pre = line_str[:max(0, sect_start - l_start)]
                     t_rect_len = min(len(line_str), sect_end - l_start) - (sect_start - l_start)
                     t_sel = line_str[max(0, sect_start - l_start) : max(0, sect_start - l_start) + max(0, t_rect_len)]
                     
                     extra_w = 0
                     if sect_end > l_end: # Selected newline
                         extra_w = font_size // 2
                     
                     w_pre = self.text_renderer.measure_text_width(t_pre, font_path, font_size)
                     w_sel = self.text_renderer.measure_text_width(t_sel, font_path, font_size) + extra_w
                     
                     sel_rect = (int(start_x + w_pre), int(current_y), int(w_sel), int(line_height))
                     self.primitive_renderer.draw_rect_primitive({"color": (50, 100, 255, 100)}, sel_rect)

            # Render Text
            if line_str:
                t_item = {
                    core.KEY_TEXT: line_str,
                    core.KEY_FONT: font_path,
                    core.KEY_FONT_SIZE: font_size,
                    core.KEY_COLOR: display_color,
                    core.KEY_WRAP: False, 
                    core.KEY_MARKUP: False 
                }
                self.text_renderer.render_text(t_item, (int(start_x), int(current_y), 2000, int(line_height)), [])

            char_idx += len(line_str) + 1
            current_y += line_height

        # --- 4. Render Cursor ---
        if item.get("focused") and not show_placeholder:
             self._draw_cursor(item, lines, start_x, start_y, line_height, font_path, font_size)

        # Restore clip
        sdl2.SDL_RenderSetClipRect(self.primitive_renderer.renderer.sdlrenderer, prev_clip if prev_clip.w > 0 else None)
        self.primitive_renderer.flush()

    def _draw_cursor(self, item, lines, start_x, start_y, line_height, font_path, font_size):
        cursor_pos = item.get("cursor_pos", 0)
        
        # Blink logic
        if int(time.time() / self._cursor_blink_rate) % 2 != 0:
            return

        curr_idx = 0
        target_line_idx = 0
        col_idx = 0
        
        found = False
        for i, line in enumerate(lines):
            line_len = len(line) + 1
            if curr_idx + line_len > cursor_pos:
                target_line_idx = i
                col_idx = cursor_pos - curr_idx
                found = True
                break
            curr_idx += line_len
            
        if not found and lines:
             target_line_idx = len(lines) - 1
             col_idx = len(lines[-1])
        
        target_line = lines[target_line_idx] if lines else ""
        prefix = target_line[:col_idx]
        w = self.text_renderer.measure_text_width(prefix, font_path, font_size)
        
        c_x = start_x + w
        c_y = start_y + target_line_idx * line_height
        
        color = item.get("text_color") or item.get(core.KEY_COLOR, (0,0,0,255))
        
        self.primitive_renderer.draw_rect_primitive(
            {"color": color},
            (int(c_x), int(c_y), 2, int(line_height))
        )
import ctypes
