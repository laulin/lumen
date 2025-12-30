import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath("src"))

from sdl_gui.window.window import Window
from sdl_gui.layers.layer import Layer
from sdl_gui.primitives.rectangle import Rectangle
import sdl2.ext

def main():
    # Create main window
    win = Window("SDL GUI Demo", 800, 600)
    
    # Create a layer
    layer = Layer(0, 0, 800, 600)
    
    # Add shapes
    rect1 = Rectangle(50, 50, 200, 100, (255, 0, 0, 255))
    rect2 = Rectangle(300, 100, 150, 150, (0, 255, 0, 255))
    
    layer.add_child(rect1)
    layer.add_child(rect2)
    
    # Add nested layer
    sub_layer = Layer(50, 300, 400, 200)
    rect3 = Rectangle(60, 310, 100, 50, (0, 0, 255, 255))
    sub_layer.add_child(rect3)
    
    # Main loop
    running = True
    while running:
        # Generate display list
        # Note: In a real app, this would be computed per frame or on change.
        # But layer.to_data() is efficient enough for this demo structure.
        display_list = [
            layer.to_data(),
            sub_layer.to_data()
        ]
        
        # Render
        win.render(display_list)
        
        # Event handling (simplified)
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False
                
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
