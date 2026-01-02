
import time
from typing import Any

from sdl_gui import core

# We need to type hint Renderer, but avoid circular import if possible.
# Using 'Any' or specific protocol is fine.

class Debug:
    """Handles debug information and rendering."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.fps_start = time.time()
        self.frame_count = 0
        self.current_fps = 0

    def update(self):
        """Update debug stats (call once per frame)."""
        if not self.enabled:
            return

        self.frame_count += 1
        now = time.time()
        if now - self.fps_start >= 1.0:
            self.current_fps = self.frame_count
            self.frame_count = 0
            self.fps_start = now

    def render(self, renderer: Any) -> None:
        """Render debug overlay."""
        if not self.enabled:
            return

        # Simple direct text rendering for debug overlay
        debug_item = {
            core.KEY_TYPE: core.TYPE_TEXT,
            core.KEY_TEXT: f"FPS: {self.current_fps}",
            core.KEY_COLOR: (0, 255, 0, 255),
            core.KEY_FONT_SIZE: 16
        }

        # Render at 10,10. Size 100x20 is arbitrary for resolving?
        # _render_text uses rect for positioning and wrapping.
        # Fixed size ensures it renders within this area.
        renderer.render_item_direct(debug_item, (10, 10, 100, 20))
