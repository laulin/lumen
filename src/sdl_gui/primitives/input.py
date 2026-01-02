from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import sdl2

from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive


class Input(BasePrimitive):
    """A text input primitive."""

    def __init__(self, x: Union[int, str], y: Union[int, str], width: Union[int, str], height: Union[int, str],
                 text: str = "",
                 placeholder: str = "",
                 font: str = None,
                 size: Union[int, str] = 16,
                 color: Tuple[int, int, int, int] = (0, 0, 0, 255),
                 background_color: Optional[Tuple[int, int, int, int]] = (255, 255, 255, 255),
                 border_color: Tuple[int, int, int, int] = (0, 0, 0, 255),
                 border_width: int = 1,
                 radius: int = 0,
                 padding: Tuple[int, int, int, int] = (5, 5, 5, 5),
                 margin: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 id: str = None,
                 listen_events: List[str] = None,
                 max_length: int = None,
                 multiline: bool = False):

        # Ensure we listen to essential events for input
        events = listen_events or []
        for evt in [core.EVENT_CLICK, core.EVENT_KEY_DOWN, core.EVENT_TEXT_INPUT,
                   core.EVENT_FOCUS, core.EVENT_BLUR, core.EVENT_MOUSE_UP,
                   core.EVENT_MOUSE_MOTION, core.EVENT_TICK]:
            if evt not in events:
                events.append(evt)

        super().__init__(x, y, width, height, padding, margin, id, events)
        self.text = text
        self.placeholder = placeholder
        self.font = font
        self.size = size
        self.color = color
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width
        self.radius = radius
        self.max_length = max_length
        self.multiline = multiline

        # Internal State
        self.cursor_pos = len(text)
        self.selection_start = None
        self.focused = False
        self.scroll_x = 0
        self.scroll_y = 0

        # Interaction State
        self.dragging = False
        self.last_click_time = 0
        self.click_count = 0
        self.last_mouse_x = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.cursor_visible = True

        # History
        self.history = []
        self.redo_stack = []

        # Callbacks
        self.on_change: Callable[[str], None] = None
        self.on_submit: Callable[[str], None] = None

    def to_data(self) -> Dict[str, Any]:
        """Generate the display list data for this input."""
        data = super().to_data()
        data[core.KEY_TYPE] = core.TYPE_INPUT
        data[core.KEY_TEXT] = self.text
        if self.placeholder:
            data["placeholder"] = self.placeholder
        if self.font:
            data[core.KEY_FONT] = self.font
        if self.size != 16:
            data[core.KEY_FONT_SIZE] = self.size
        if self.color != (0, 0, 0, 255):
            data[core.KEY_COLOR] = self.color
        if self.background_color != (255, 255, 255, 255):
            data["background_color"] = self.background_color

        if self.border_color != (0, 0, 0, 255) and self.border_width > 0:
            data[core.KEY_BORDER_COLOR] = self.border_color
            data[core.KEY_BORDER_WIDTH] = self.border_width
        elif self.border_width != 1 and self.border_width > 0:
            data[core.KEY_BORDER_WIDTH] = self.border_width

        if self.radius > 0:
            data[core.KEY_RADIUS] = self.radius
        if self.multiline:
            data["multiline"] = self.multiline

        # Internal state needed for rendering
        if self.cursor_pos != 0:
            data["cursor_pos"] = self.cursor_pos
        if self.selection_start is not None:
            data["selection_start"] = self.selection_start
        if self.focused:
            data["focused"] = self.focused
        if not self.cursor_visible:
            data["cursor_visible"] = self.cursor_visible
        if self.scroll_x != 0:
            data["scroll_x"] = self.scroll_x
        if self.scroll_y != 0:
            data["scroll_y"] = self.scroll_y

        return data

    def handle_event(self, event: Dict[str, Any], context: Any = None):
        """
        Handle events dispatched to this component.
        Context usually contains helpers like 'measure_text_width'.
        """
        evt_type = event.get("type")

        if evt_type == core.EVENT_FOCUS:
            self.focused = True
        elif evt_type == core.EVENT_BLUR:
            self.focused = False
            self.selection_start = None
            self.dragging = False

        elif evt_type == core.EVENT_TEXT_INPUT and self.focused:
            text = event.get("text", "")
            self._insert_text(text, context)

        elif evt_type == core.EVENT_KEY_DOWN and self.focused:
            key_sym = event.get("key_sym")
            mod = event.get("mod", 0)
            self._handle_key(key_sym, mod, context)

        elif evt_type == core.EVENT_CLICK:
             if context and "local_x" in event:
                 local_x = event.get("local_x", 0)
                 local_y = event.get("local_y", 0)

                 # Double/Triple Click Logic
                 now = sdl2.SDL_GetTicks()
                 if self.click_count > 0 and now - self.last_click_time < 500:
                     self.click_count += 1
                 else:
                     self.click_count = 1
                 self.last_click_time = now

                 self.focused = True
                 self.dragging = True
                 self.last_mouse_x = local_x
                 self.last_mouse_y = local_y

                 if self.click_count == 2:
                     # Double click: Select Word
                     self._set_cursor_from_mouse(local_x, local_y, context)
                     self._select_word_at_cursor()
                     # In drag mode, we might want to extend word selection?
                     # For simplicity, double click selects word, subsequent drag extends char by char or word by word?
                     # Standard behavior: drag after double click extends by word. Complex.
                     # Let's stick to simple drag first.
                     self.dragging = False # Stop dragging on double click to avoid immediate override?
                     # Actually standard is drag selection. But let's keep it simple.
                 elif self.click_count == 3:
                     # Triple click: Select All
                     self.selection_start = 0
                     self.cursor_pos = len(self.text)
                     self.dragging = False
                 else:
                     # Single click
                     shift = (sdl2.SDL_GetModState() & sdl2.KMOD_SHIFT)
                     if shift:
                         if self.selection_start is None: self.selection_start = self.cursor_pos
                     else:
                         self.selection_start = self.cursor_pos # Start selection anchor

                     self._set_cursor_from_mouse(local_x, local_y, context)
                     if not shift:
                         self.selection_start = self.cursor_pos # If not shift, anchor = cursor

        elif evt_type == core.EVENT_MOUSE_UP:
            self.dragging = False

        elif evt_type == core.EVENT_MOUSE_MOTION:
            if self.dragging and context and "local_x" in event:
                 local_x = event.get("local_x", 0)
                 local_y = event.get("local_y", 0)
                 self.last_mouse_x = local_x
                 self.last_mouse_y = local_y

                 # Update selection
                 # We keep selection_start (anchor) fixed, move cursor_pos.
                 self._set_cursor_from_mouse(local_x, local_y, context)
                 # Ensure selection_start was set on click (it was).

        elif evt_type == core.EVENT_TICK:
            # Blink Logic
            ticks = event.get("ticks", sdl2.SDL_GetTicks())
            self.cursor_visible = (ticks // 500) % 2 == 0

            if self.dragging and self.focused and context:
                 # Autoscroll
                 scroll_speed = 5
                 changed = False

                 # Horizontal
                 if not self.multiline:
                     if self.last_mouse_x < 0:
                         self.scroll_x -= scroll_speed
                         changed = True
                     elif self.last_mouse_x > self.width: # approx width
                         self.scroll_x += scroll_speed
                         changed = True
                     if self.scroll_x < 0: self.scroll_x = 0

                 # Vertical
                 if self.multiline:
                     if self.last_mouse_y < 0:
                         self.scroll_y -= scroll_speed
                         changed = True
                     elif self.last_mouse_y > self.height:
                         self.scroll_y += scroll_speed
                         changed = True
                     if self.scroll_y < 0: self.scroll_y = 0

                 if changed:
                     # Re-eval cursor pos based on new scroll
                     self._set_cursor_from_mouse(self.last_mouse_x, self.last_mouse_y, context)

    def _insert_text(self, text, context=None):
        if self.max_length and len(self.text) + len(text) > self.max_length:
             # Truncate
             allowed = self.max_length - len(self.text)
             if allowed <= 0: return
             text = text[:allowed]

        # Delete selection first if any
        if self.selection_start is not None:
             self._delete_selection()

        self.text = self.text[:self.cursor_pos] + text + self.text[self.cursor_pos:]
        self.cursor_pos += len(text)

        if context: self._update_scroll(context)
        if self.on_change: self.on_change(self.text)

    def _delete_selection(self):
        if self.selection_start is None: return

        start = min(self.cursor_pos, self.selection_start)
        end = max(self.cursor_pos, self.selection_start)

        self.text = self.text[:start] + self.text[end:]
        self.cursor_pos = start
        self.selection_start = None
        if self.on_change: self.on_change(self.text)

    def _handle_key(self, key_sym, mod, context):
        ctrl = (mod & sdl2.KMOD_CTRL)
        shift = (mod & sdl2.KMOD_SHIFT)

        if key_sym == sdl2.SDLK_BACKSPACE:
            if self.selection_start is not None:
                self._delete_selection()
            elif ctrl:
                 # Delete Word Left
                 target = self._find_prev_word_start(self.cursor_pos)
                 self.text = self.text[:target] + self.text[self.cursor_pos:]
                 self.cursor_pos = target
                 if context: self._update_scroll(context)
                 if self.on_change: self.on_change(self.text)
            elif self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
                if context: self._update_scroll(context)
                if self.on_change: self.on_change(self.text)

        elif key_sym == sdl2.SDLK_DELETE:
            if self.selection_start is not None:
                self._delete_selection()
            elif self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                if context: self._update_scroll(context)
                if self.on_change: self.on_change(self.text)

        elif key_sym == sdl2.SDLK_LEFT:
            if shift:
                if self.selection_start is None: self.selection_start = self.cursor_pos
            else:
                self.selection_start = None

            if ctrl:
                self.cursor_pos = self._find_prev_word_start(self.cursor_pos)
                if context: self._update_scroll(context)
            elif self.cursor_pos > 0:
                self.cursor_pos -= 1
                if context: self._update_scroll(context)
            elif not shift and self.selection_start is None:
                pass

        elif key_sym == sdl2.SDLK_RIGHT:
            if shift:
                 if self.selection_start is None: self.selection_start = self.cursor_pos
            else:
                 self.selection_start = None

            if ctrl:
                self.cursor_pos = self._find_next_word_start(self.cursor_pos)
                if context: self._update_scroll(context)
            elif self.cursor_pos < len(self.text):
                self.cursor_pos += 1
                if context: self._update_scroll(context)

        elif key_sym == sdl2.SDLK_UP:
            if shift:
                if self.selection_start is None: self.selection_start = self.cursor_pos
            else:
                self.selection_start = None

            if self.multiline:
                line, col = self._get_line_col(self.text, self.cursor_pos)
                if line > 0:
                    self.cursor_pos = self._get_cursor_from_line_col(self.text, line - 1, col)
                    if context: self._update_scroll(context)

        elif key_sym == sdl2.SDLK_DOWN:
             if shift:
                if self.selection_start is None: self.selection_start = self.cursor_pos
             else:
                self.selection_start = None

             if self.multiline:
                line, col = self._get_line_col(self.text, self.cursor_pos)
                total_lines = self.text.count('\n') + 1
                if line < total_lines - 1:
                    self.cursor_pos = self._get_cursor_from_line_col(self.text, line + 1, col)
                    if context: self._update_scroll(context)

        elif key_sym == sdl2.SDLK_HOME:
            if shift:
                if self.selection_start is None: self.selection_start = self.cursor_pos
            else:
                self.selection_start = None
            self.cursor_pos = 0
            if context: self._update_scroll(context)

        elif key_sym == sdl2.SDLK_END:
             if shift:
                 if self.selection_start is None: self.selection_start = self.cursor_pos
             else:
                 self.selection_start = None
             self.cursor_pos = len(self.text)
             if context: self._update_scroll(context)

        elif key_sym == sdl2.SDLK_a and ctrl:
            self.selection_start = 0
            self.cursor_pos = len(self.text)

        elif key_sym == sdl2.SDLK_c and ctrl:
            if self.selection_start is not None:
                start = min(self.cursor_pos, self.selection_start)
                end = max(self.cursor_pos, self.selection_start)
                clipboard_text = self.text[start:end]
                sdl2.SDL_SetClipboardText(clipboard_text.encode('utf-8'))

        elif key_sym == sdl2.SDLK_v and ctrl:
             if  sdl2.SDL_HasClipboardText():
                 text = sdl2.SDL_GetClipboardText().decode('utf-8')
                 if text: self._insert_text(text, context)

        elif key_sym == sdl2.SDLK_x and ctrl:
            if self.selection_start is not None:
                self._snapshot_history()
                start = min(self.cursor_pos, self.selection_start)
                end = max(self.cursor_pos, self.selection_start)
                clipboard_text = self.text[start:end]
                sdl2.SDL_SetClipboardText(clipboard_text.encode('utf-8'))
                self._delete_selection()
                if context: self._update_scroll(context)

        elif key_sym == sdl2.SDLK_z and ctrl:
            if shift: # Redo
                self._redo()
            else: # Undo
                self._undo()
            if context: self._update_scroll(context)

        elif key_sym == sdl2.SDLK_y and ctrl:
             self._redo()
             if context: self._update_scroll(context)

        elif key_sym == sdl2.SDLK_RETURN or key_sym == sdl2.SDLK_KP_ENTER:
            if self.multiline:
                self._snapshot_history()
                self._insert_text("\n", context, snapshot=False) # already snapshotted
            elif self.on_submit:
                self.on_submit(self.text)

    def _snapshot_history(self):
        # Limit history size?
        if len(self.history) > 50: self.history.pop(0)
        self.history.append((self.text, self.cursor_pos, self.selection_start))
        self.redo_stack.clear()

    def _undo(self):
        if not self.history: return

        # Save current state to redo
        self.redo_stack.append((self.text, self.cursor_pos, self.selection_start))

        # Pop previous
        state = self.history.pop()
        self.text, self.cursor_pos, self.selection_start = state

    def _redo(self):
        if not self.redo_stack: return

        # Save current to history logic?
        # Actually standard redo pops from redo stack and pushes to history.

        self.history.append((self.text, self.cursor_pos, self.selection_start))
        state = self.redo_stack.pop()
        self.text, self.cursor_pos, self.selection_start = state

    def _insert_text(self, text, context=None, snapshot=True):
        if snapshot: self._snapshot_history()

        if self.max_length and len(self.text) + len(text) > self.max_length:
             # Truncate
             allowed = self.max_length - len(self.text)
             if allowed <= 0: return
             text = text[:allowed]

        # Delete selection first if any
        if self.selection_start is not None:
             self._delete_selection(snapshot=False)

        self.text = self.text[:self.cursor_pos] + text + self.text[self.cursor_pos:]
        self.cursor_pos += len(text)

        if context: self._update_scroll(context)
        if self.on_change: self.on_change(self.text)

    def _delete_selection(self, snapshot=True):
        if snapshot: self._snapshot_history()
        if self.selection_start is None: return

        start = min(self.cursor_pos, self.selection_start)
        end = max(self.cursor_pos, self.selection_start)

        self.text = self.text[:start] + self.text[end:]
        self.cursor_pos = start
        self.selection_start = None
        if self.on_change: self.on_change(self.text)

    def _select_word_at_cursor(self):
        # Find start
        # Scan back from cursor_pos.
        # If we are at end of word, we want to select current word.
        # If we are in middle, same.
        # If we are at start of word, duplicate logic?

        # Original logic: self._find_prev_word_start(self.cursor_pos + 1)
        # This was intending to include the character AT cursor_pos in backward scan.
        # Safe way: Clamp to len(text).

        scan_pos = min(self.cursor_pos + 1, len(self.text))
        start = self._find_prev_word_start(scan_pos)

        # Find end
        end = self._find_next_word_end(start)

        self.selection_start = start
        self.cursor_pos = end

    def _find_prev_word_start(self, pos):
        if pos <= 0: return 0
        i = pos - 1

        # Clamp i if it exceeds bounds (though logic above should handle it)
        if i >= len(self.text): i = len(self.text) - 1

        # Skip whitespace backwards
        while i >= 0 and self.text[i].isspace():
            i -= 1
        # Skip alphanumeric backwards
        while i >= 0 and not self.text[i].isspace():
            i -= 1

        return i + 1

    def _find_next_word_start(self, pos):
        if pos >= len(self.text): return len(self.text)
        i = pos
        # Skip current word
        while i < len(self.text) and not self.text[i].isspace():
            i += 1
        # Skip spaces
        while i < len(self.text) and self.text[i].isspace():
            i += 1
        return i

    def _find_next_word_end(self, pos):
        if pos >= len(self.text): return len(self.text)
        i = pos
        while i < len(self.text) and not self.text[i].isspace():
            i += 1
        return i

    def _update_scroll(self, context):
        if not hasattr(context, 'measure_text_width'): return

        # Line Height Heuristic (match renderer)
        line_height = self.size + 4

        # Calculate cursor Pixel Position
        # Single Line Logic
        if not self.multiline:
            cursor_px = context.measure_text_width(self.text[:self.cursor_pos], self.font, self.size)

            # Visible Width Area
            pad_l = self.padding[3] if isinstance(self.padding, (tuple, list)) else self.padding
            pad_r = self.padding[1] if isinstance(self.padding, (tuple, list)) else self.padding

            visible_w = (self.width if isinstance(self.width, int) else 200) - pad_l - pad_r

            # Scroll Logic
            if cursor_px < self.scroll_x:
                 self.scroll_x = cursor_px
            elif cursor_px > self.scroll_x + visible_w:
                 self.scroll_x = cursor_px - visible_w

            if self.scroll_x < 0: self.scroll_x = 0

        else:
            # Multiline Logic (Vertical Scroll)
            line, col = self._get_line_col(self.text, self.cursor_pos)
            cursor_y = line * line_height

            pad_t = self.padding[0] if isinstance(self.padding, (tuple, list)) else self.padding
            pad_b = self.padding[2] if isinstance(self.padding, (tuple, list)) else self.padding
            visible_h = (self.height if isinstance(self.height, int) else 100) - pad_t - pad_b

            if cursor_y < self.scroll_y:
                self.scroll_y = cursor_y
            elif cursor_y + line_height > self.scroll_y + visible_h:
                self.scroll_y = cursor_y + line_height - visible_h

            if self.scroll_y < 0: self.scroll_y = 0

    def _get_line_col(self, text, cursor_pos):
        # Determine line and col of cursor
        lines = text.split('\n')
        curr = 0
        for i, line in enumerate(lines):
            line_len = len(line) + 1 # +1 for newline
            if curr + line_len > cursor_pos: # Cursor in this line (or before newline)
                return i, cursor_pos - curr
            elif curr + line_len == cursor_pos and i == len(lines) - 1:
                # End of last line
                return i, len(line)
            curr += line_len
        return len(lines)-1, len(lines[-1])

    def _get_cursor_from_line_col(self, text, line_idx, col_idx):
        lines = text.split('\n')
        clamp_line = max(0, min(line_idx, len(lines)-1))
        target_line = lines[clamp_line]
        clamp_col = max(0, min(col_idx, len(target_line)))

        # Calculate pos
        curr = 0
        for i in range(clamp_line):
             curr += len(lines[i]) + 1
        return curr + clamp_col

    def _set_cursor_from_mouse(self, local_x: int, local_y: int, context):
        if not hasattr(context, 'measure_text_width'): return

        # Adjust for scroll
        effective_x = local_x + self.scroll_x
        effective_y = local_y + self.scroll_y

        # Determine target line
        target_line_idx = 0
        if self.multiline:
            pad_t = self.padding[0] if isinstance(self.padding, (tuple, list)) else self.padding
            line_height = self.size + 4
            # Rel y from content start
            rel_y = effective_y - pad_t
            if rel_y < 0: rel_y = 0
            target_line_idx = int(rel_y // line_height)

        lines = self.text.split('\n')
        # Clamp line index
        if target_line_idx >= len(lines):
            target_line_idx = len(lines) - 1
        if target_line_idx < 0: target_line_idx = 0

        target_line = lines[target_line_idx]

        # Scan char in this line
        best_col = 0
        min_diff = float('inf')

        for i in range(len(target_line) + 1):
            sub = target_line[:i]
            w = context.measure_text_width(sub, self.font, self.size)
            diff = abs(w - effective_x)
            if diff < min_diff:
                min_diff = diff
                best_col = i
            else:
                break

        # Convert line/col to absolute cursor pos
        # Count chars before this line
        abs_pos = 0
        for i in range(target_line_idx):
            abs_pos += len(lines[i]) + 1 # +1 for newline

        self.cursor_pos = abs_pos + best_col
