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
        events={
            core.EVENT_CLICK: on_click
        }
    )
    
    # Note: Since primitives are immutable-ish (we rebuild data), 
    # we need to ensure the data reflects the state.
    # The 'rect' object's color attribute won't auto-update if we just change the list `rect_color`.
    # But for the demo, we can rebuild the rect or just modify the object before render.

    running = True
    while running:
        # Update rect color from state
        rect.color = tuple(rect_color)
        
        layer.children = [rect] # Reset children
        
        display_list = [layer.to_data()]
        win.render(display_list)
        
        events = sdl2.ext.get_events()
        # Dispatch to GUI
        win.dispatch_events(events)
        
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
