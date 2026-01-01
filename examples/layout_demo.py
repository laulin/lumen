import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdl_gui.window.window import Window
from sdl_gui.layers.layer import Layer
from sdl_gui.layouts.vbox import VBox
from sdl_gui.layouts.hbox import HBox
from sdl_gui.primitives.rectangle import Rectangle
import sdl2.ext

def main():
    win = Window("Layout Demo", 800, 600)
    
    # Root layer
    layer = Layer(0, 0, "100%", "100%")
    
    # Main VBox with padding
    vbox = VBox(x=0, y=0, width="100%", height="100%", padding=(20, 20, 20, 20))
    layer.add_child(vbox)
    
    # Header (HBox)
    header = HBox(x=0, y=0, width="100%", height=100, padding=(10, 10, 10, 10))
    header.add_child(Rectangle(0, 0, 100, "100%", (200, 50, 50, 255), margin=(0, 10, 0, 0))) # Logo
    header.add_child(Rectangle(0, 0, "60%", "100%", (50, 50, 200, 255))) # Banner
    vbox.add_child(header)
    
    # Content (HBox)
    content = HBox(x=0, y=0, width="100%", height="50%", padding=(10, 0, 10, 0), margin=(20, 0, 0, 0))
    content.add_child(Rectangle(0, 0, "30%", "100%", (100, 100, 100, 255), margin=(0, 20, 0, 0))) # Sidebar
    content.add_child(Rectangle(0, 0, "60%", "100%", (200, 200, 200, 255))) # Main content
    vbox.add_child(content)

    # Footer (Rectangle)
    # Note: VBox stacks them.
    vbox.add_child(Rectangle(0, 0, "100%", 50, (50, 50, 50, 255), margin=(20, 0, 0, 0)))
    
    running = True
    while running:
        win.render([layer.to_data()])
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False
        sdl2.SDL_Delay(8)
                
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
