
from typing import Any, Dict, List, Optional, Tuple

import sdl2
import sdl2.ext
from sdl2 import sdlttf

from sdl_gui import core, markdown, utils
from sdl_gui.rendering.primitive_renderer import PrimitiveRenderer


class TextRenderer:
    """
    Handles rendering of text and rich text.
    Manages font caches and text texture caches.
    """

    def __init__(self, renderer: sdl2.ext.Renderer, primitive_renderer: PrimitiveRenderer):
        self.renderer = renderer
        self.primitive_renderer = primitive_renderer
        self.ttf_available = True

        if not sdlttf.TTF_WasInit():
            if sdlttf.TTF_Init() == -1:
                print("TTF_Init: %s" % sdl2.SDL_GetError())
                self.ttf_available = False

        # Caches
        self._font_cache: Dict[str, sdl2.ext.FontManager] = {}
        self._text_texture_cache: Dict[Tuple, Tuple[sdl2.ext.Texture, Tuple[int, int]]] = {}
        self._text_measurement_cache: Dict[Tuple, Tuple[int, int]] = {}
        self._rich_text_layout_cache: Dict[Tuple, Any] = {}

    def clear_caches(self):
        """Clear all text-related caches."""
        self._text_texture_cache.clear()
        self._text_measurement_cache.clear()
        self._rich_text_layout_cache.clear()
        # Note: We keep font managers as they are expensive to reload

    def render_text(
        self,
        item: Dict[str, Any],
        rect: Tuple[int, int, int, int],
        hit_list: List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]]
    ) -> None:
        """Render text item (plain or rich)."""
        self.primitive_renderer.flush()

        if not self.ttf_available or not item.get(core.KEY_TEXT, ""):
            return

        if item.get(core.KEY_MARKUP, True):
            self._render_rich_text(item, rect, hit_list)
        else:
            lines, settings = self._layout_plain_text(item, rect)
            self._draw_plain_text_lines(lines, settings, rect)

    def measure_text_width(self, text: str, font_path: str = None, font_size: int = 16) -> int:
        """Public helper to measure text width."""
        font_path = font_path or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        w, _ = self._measure_text_cached(text, font_path, font_size)
        return w

    def _get_font_manager(self, font_path: str, size: int, color: Tuple[int, int, int, int], bold: bool = False) -> Optional[sdl2.ext.FontManager]:
        cache_key = f"{font_path}_{size}_{color}_{bold}"
        font_manager = self._font_cache.get(cache_key)
        if not font_manager:
            try:
                # Ensure color is hashable/tuple
                c_tuple = tuple(color) if isinstance(color, (list, tuple)) else (0,0,0,255)
                # SDL2 FontManager expects color as specific type or tuple?
                # Usually it takes (r,g,b,a) or Color object.
                font_manager = sdl2.ext.FontManager(font_path, size=size, color=c_tuple)
                if bold and hasattr(font_manager, "font"):
                    sdlttf.TTF_SetFontStyle(font_manager.font, sdlttf.TTF_STYLE_BOLD)
                self._font_cache[cache_key] = font_manager
            except Exception:
                return None
        return font_manager

    def _measure_text_cached(
        self, text: str, font_path: str, size: int, bold: bool = False
    ) -> Tuple[int, int]:
        cache_key = (font_path, size, text, bold)
        cached = self._text_measurement_cache.get(cache_key)
        if cached is not None:
            return cached

        # Use a neutral color for measurement
        fm = self._get_font_manager(font_path, size, (0, 0, 0, 255), bold)
        if fm:
            try:
                 surface = fm.render(text)
                 result = (surface.w, surface.h) if surface else (0, 0)
            except Exception:
                 result = (0, 0)
        else:
            result = (0, 0)

        self._text_measurement_cache[cache_key] = result
        return result

    def _get_resolved_font_size(self, item, parent_h):
        raw = item.get(core.KEY_FONT_SIZE, 16)
        s = utils.resolve_val(raw, parent_h) if parent_h > 0 else (raw if isinstance(raw, int) else 16)
        return s if s > 0 else 16

    # --- Plain Text ---

    def _layout_plain_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]) -> Tuple[List[str], Dict]:
        text = item.get(core.KEY_TEXT, "")
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        size = self._get_resolved_font_size(item, rect[3])
        color = item.get(core.KEY_COLOR, (0, 0, 0, 255))
        if len(color) == 3: color = (*color, 255)

        fm = self._get_font_manager(font_path, size, color)
        if not fm: return [], {}

        def measure(s):
            surf = fm.render(s)
            return (surf.w if surf else 0, surf.h if surf else 0)

        lines = [text] if not item.get(core.KEY_WRAP, True) else self._wrap_text(text, measure, rect[2])
        _, lh = measure("Tg")
        lh = max(lh, size) # Ensure at least size height

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
        max_l = max(1, int(max_h // line_h))
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

        # Ensure color is tuple
        color_key = tuple(settings["color"]) if isinstance(settings["color"], list) else settings["color"]

        for line in lines:
            if cy > max_y: break
            cache_key = (settings["font_path"], settings["size"], color_key, line)
            cached = self._text_texture_cache.get(cache_key)

            if cached:
                texture, (tw, th) = cached
            else:
                s = settings["fm"].render(line)
                if not s: continue
                texture = sdl2.ext.Texture(self.renderer, s)
                tw, th = texture.size
                self._text_texture_cache[cache_key] = (texture, (tw, th))

            tx = rect[0]
            if settings["align"] == "center": tx += (rect[2] - tw) // 2
            elif settings["align"] == "right": tx += rect[2] - tw
            self.renderer.copy(texture, dstrect=(tx, cy, tw, th))
            cy += settings["line_h"]

    # --- Rich Text ---

    def _render_rich_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], hit_list: List) -> None:
        lines, settings = self._layout_rich_text(item, rect)
        self._draw_rich_text_lines(lines, settings, rect, item, hit_list)

    def _layout_rich_text(self, item: Dict[str, Any], rect: Tuple[int, int, int, int]):
        font_path = item.get(core.KEY_FONT) or "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        size = self._get_resolved_font_size(item, rect[3])
        base_color = item.get(core.KEY_COLOR, (0, 0, 0, 255))
        if len(base_color) == 3: base_color = (*base_color, 255)
        text_content = item.get(core.KEY_TEXT, "")

        # Check cache
        cache_key = (text_content, rect[2], font_path, size, tuple(base_color))
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
                # Optimization to not split every word if no wrap?
                # But we assume wrapping logic needs words.
                words = line.split(" ")
                for j, w in enumerate(words):
                    suf = " " if j < len(words) - 1 else ""
                    if w+suf: chunked.append((w+suf, seg))
                if i < len(lines) - 1: chunked.append(("\n", seg))
        return chunked

    def _draw_rich_text_lines(self, lines, settings, rect, item, hit_list):
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
                    hit_list.append(((lx, curr_y, w, h), {
                        "type": "link", "target": seg.link_target,
                        core.KEY_LISTEN_EVENTS: [core.EVENT_CLICK]
                    }))
                lx += w
            curr_y += line_h

    def _draw_rich_chunk(self, txt, seg, x, y, w, h, settings):
        # Cache key needs to account for color tuple
        msg_color = tuple(seg.color) if isinstance(seg.color, list) else seg.color
        cache_key = (settings["font_path"], settings["size"], msg_color, txt, seg.bold)
        cached = self._text_texture_cache.get(cache_key)

        if cached:
            texture, tex_size = cached
        else:
            texture = None
            tex_size = None
            fm = self._get_font_manager(settings["font_path"], settings["size"], seg.color, seg.bold)
            if fm:
                surf = fm.render(txt)
                if surf:
                    texture = sdl2.ext.Texture(self.renderer.sdlrenderer, surf)
                    tex_size = texture.size
                    self._text_texture_cache[cache_key] = (texture, tex_size)

        if texture:
            self.renderer.copy(texture, dstrect=(x, y, *tex_size))

    # Measurement helpers exposed for layout engine (Renderer)

    def measure_rich_text_height(self, item: Dict[str, Any], width: int, parent_h: int) -> int:
        lines, settings = self._layout_rich_text(item, (0, 0, width, parent_h))
        total_h = 0
        lh = settings["line_h"]
        for line in lines:
             line_max_h = lh
             for _, _, _, h in line: line_max_h = max(line_max_h, h)
             total_h += line_max_h
        return total_h

    def measure_plain_text_height(self, item: Dict[str, Any], width: int, parent_h: int) -> int:
        # We can reuse _layout_plain_text but we need a dummy rect
        # rect = (x, y, w, h). We only care about w and h for resolution.
        lines, settings = self._layout_plain_text(item, (0, 0, width, parent_h))
        return len(lines) * settings["line_h"]

