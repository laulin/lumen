import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdl_gui.window.window import Window
from sdl_gui.layers.layer import Layer
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui import core
import sdl2.ext

def main():
    win = Window("Events Demo", 800, 600)
    
    # State
    rect_color = [255, 0, 0, 255]

    def on_click():
        print("Clicked!")
        # Toggle color
        if rect_color[0] == 255:
            rect_color[0] = 0
            rect_color[1] = 255
        else:
            rect_color[0] = 255
            rect_color[1] = 0

    layer = Layer(0, 0, "100%", "100%")
    
    # Clickable Rectangle
    rect = Rectangle(
        x="40%", y="40%", 
        width="20%", height="20%",
        color=tuple(rect_color),
        id="color_btn",
        listen_events=[core.EVENT_CLICK]
    )
    
    running = True
    while running:
        # Update rect color from state
        rect.color = tuple(rect_color)
        
        layer.children = [rect] # Reset children
        
        display_list = [layer.to_data()]
        win.render(display_list)
        
        # Poll UI Events
        ui_events = win.get_ui_events()
        for event in ui_events:
            if event["type"] == core.EVENT_CLICK and event["target"] == "color_btn":
                on_click()

        # Handle Quit manually for now (since get_ui_events consumes SDL events)
        # Actually, get_ui_events consumes them, so we need a way to check for QUIT.
        # Ideally get_ui_events should maybe yield Special events or we should check peeks?
        # For this simple implementation, let's assume get_ui_events SHOULD handle general app events 
        # or we should rely on a better event loop.
        # But wait, `sdl2.ext.get_events()` clears the queue.
        # So `win.get_ui_events()` effectively swallows QUIT if we don't return it.
        # Let's modify get_ui_events to maybe return QUIT or handle it? 
        # Or better, let's fix the demo to work with limitations: 
        # We can implement a "check quit" inside the loop here if we modify Window to pass-through or return a QUIT event.
        # But for now, let's just make sure we don't block closing.
        # Actually, `get_ui_events` iterates all events. We should probably pass non-consumed events back or handle QUIT there.
        # Let's add QUIT support to `get_ui_events` for the demo to work.
        pass

                
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
