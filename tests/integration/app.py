import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from sdl_gui.window.window import Window
from sdl_gui import core

def run_app():
    # Use software renderer for compatibility with dummy driver
    import sdl2
    with Window("Flexbox Integration", 800, 600, debug=True, renderer_flags=sdl2.SDL_RENDERER_SOFTWARE) as win:
        display_list = [
            {
                core.KEY_TYPE: core.TYPE_FLEXBOX,
                core.KEY_RECT: [0, 0, "100%", "100%"],
                core.KEY_COLOR: (10, 10, 10, 255),
                core.KEY_FLEX_DIRECTION: "column",
                core.KEY_CHILDREN: [
                    # Row 1: Space Between
                    {
                        core.KEY_TYPE: core.TYPE_FLEXBOX,
                        core.KEY_RECT: [0, 0, "100%", 100],
                        core.KEY_FLEX_DIRECTION: "row",
                        core.KEY_JUSTIFY_CONTENT: "space_between",
                        core.KEY_COLOR: (30, 30, 30, 255),
                        core.KEY_CHILDREN: [
                            {
                                core.KEY_TYPE: core.TYPE_RECT,
                                core.KEY_ID: "red_box",
                                core.KEY_RECT: [0, 0, 50, 50],
                                core.KEY_COLOR: (255, 0, 0, 255)
                            },
                            {
                                core.KEY_TYPE: core.TYPE_RECT,
                                core.KEY_ID: "green_box",
                                core.KEY_RECT: [0, 0, 50, 50],
                                core.KEY_COLOR: (0, 255, 0, 255)
                            }
                        ]
                    },
                    # Row 2: Center Alignment
                    {
                        core.KEY_TYPE: core.TYPE_FLEXBOX,
                        core.KEY_RECT: [0, 0, "100%", 200],
                        core.KEY_FLEX_DIRECTION: "row",
                        core.KEY_JUSTIFY_CONTENT: "center",
                        core.KEY_ALIGN_ITEMS: "center",
                        core.KEY_COLOR: (40, 40, 40, 255),
                        core.KEY_CHILDREN: [
                            {
                                core.KEY_TYPE: core.TYPE_RECT,
                                core.KEY_ID: "blue_box",
                                core.KEY_RECT: [0, 0, 100, 100],
                                core.KEY_COLOR: (0, 0, 255, 255)
                            }
                        ]
                    },
                    # Row 3: Flex End
                    {
                        core.KEY_TYPE: core.TYPE_FLEXBOX,
                        core.KEY_RECT: [0, 0, "100%", 100],
                        core.KEY_FLEX_DIRECTION: "row",
                        core.KEY_JUSTIFY_CONTENT: "flex_end",
                        core.KEY_ALIGN_ITEMS: "flex_end",
                        core.KEY_COLOR: (50, 50, 50, 255),
                        core.KEY_CHILDREN: [
                            {
                                core.KEY_TYPE: core.TYPE_RECT,
                                core.KEY_ID: "yellow_box",
                                core.KEY_RECT: [0, 0, 40, 40],
                                core.KEY_COLOR: (255, 255, 0, 255)
                            }
                        ]
                    }
                ]
            }
        ]
        
        running = True
        while running:
            events = win.get_ui_events()
            for event in events:
                if event.get("type") == core.EVENT_QUIT:
                    running = False
            
            win.render(display_list)
            # Short sleep to avoid maxing CPU and allow debug server to breathe
            time.sleep(0.01)

if __name__ == "__main__":
    run_app()
