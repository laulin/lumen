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
    
    # Layer 1 (Bottom)
    layer1 = Layer(0, 0, "100%", "100%")
    rect1 = Rectangle(
        x="20%", y="20%", 
        width="40%", height="40%",
        color=(255, 0, 0, 255), # Red
        id="rect_bottom",
        listen_events=[core.EVENT_CLICK]
    )
    layer1.children = [rect1]

    # Layer 2 (Top)
    layer2 = Layer(0, 0, "100%", "100%")
    rect2 = Rectangle(
        x="40%", y="40%", 
        width="40%", height="40%",
        color=(0, 0, 255, 255), # Blue
        id="rect_top",
        listen_events=[core.EVENT_CLICK]
    )
    layer2.children = [rect2]
    
    print("Click on rectangles. Blue is on top of Red.")

    running = True
    while running:
        # Display list with both layers (layer2 is drawn last -> on top)
        display_list = [layer1.to_data(), layer2.to_data()]
        win.render(display_list)
        
        # Poll UI Events
        ui_events = win.get_ui_events()
        for event in ui_events:
            if event["type"] == core.EVENT_QUIT:
                running = False
            elif event["type"] == core.EVENT_CLICK:
                target = event["target"]
                print(f"Clicked: {target}")
                
                # Visual feedback
                if target == "rect_top":
                    print("  -> Top Blue Rect hit!")
                elif target == "rect_bottom":
                    print("  -> Bottom Red Rect hit!")

        # Handle Quit manually (simple check)
        # Note: Window.get_ui_events() already drained events.
        # But just in case any residuals:
        events = sdl2.ext.get_events()
        for event in events:
             pass
        sdl2.SDL_Delay(8)

                
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
