import sys
import os
from pprint import pprint 

# Ensure src is in path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


from sdl_gui.window.window import Window
from sdl_gui.layers.layer import Layer
from sdl_gui.primitives.rectangle import Rectangle
import sdl2.ext

def main():
    # Create main window
    win = Window("SDL GUI Demo", 800, 600)
    
    # Create a layer
    layer = Layer(0, 0, "100%", "100%")
    
    # Add shapes
    rect1 = Rectangle("10%", "10%", "30%", "20%", (255, 0, 0, 255))
    rect2 = Rectangle("50%", "10%", "30%", "20%", (0, 255, 0, 255))
    
    layer.add_child(rect1)
    layer.add_child(rect2)
    
    # Add nested layer
    sub_layer = Layer("10%", "50%", "80%", "40%")
    rect3 = Rectangle("10%", "10%", "80%", "80%", (0, 0, 255, 255))
    sub_layer.add_child(rect3)

    # Generate display list
    # Note: In a real app, this would be computed per frame or on change.
    # But layer.to_data() is efficient enough for this demo structure.
    display_list = [
        layer.to_data(),
        sub_layer.to_data()
    ]
    pprint(display_list)
    
    # Main loop
    running = True
    while running:
        # Render
        win.render(display_list)
        
        # Event handling (simplified)
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False
                
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
