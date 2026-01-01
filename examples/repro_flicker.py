import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from sdl_gui.window.window import Window
from sdl_gui.primitives import Input, Rectangle

def main():
    window = Window("Flicker Repro", 400, 300)
    with window:
        Rectangle(0, 0, 400, 300, color=(200, 200, 200)) # distinct bg
        Input(50, 50, 300, 100, placeholder="Multiline Flicker Test", multiline=True, id="input_test")
    
    window.show()
    
    # Auto-focus for automated testing
    import time
    start_time = time.time()
    # Mock focus
    window.root_children[1].focused = True
    
    running = True
    while running:
        # Auto-close after 2 seconds
        if time.time() - start_time > 2:
            running = False
            
        events = window.get_ui_events()
        for e in events:
            if e["type"] == "QUIT": running = False
            
            # Dispatch to input (simplified)
            if e.get("target") == "input_test":
               window.root_children[1].handle_event(e, window)
               
        # RENDER
        dl = window.get_root_display_list()
        window.render(dl)
               
if __name__ == "__main__":
    main()
