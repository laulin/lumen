import sys
import os
import sdl2.ext

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdl_gui.window.window import Window
from sdl_gui.layers.layer import Layer
from sdl_gui.primitives.responsive_text import ResponsiveText

def main():
    win = Window("Text Demo", 800, 600)
    win.show()

    layer = Layer(0, 0, "100%", "100%")
    
    # Text items
    txt1 = ResponsiveText("10%", "10%", "80%", "50", 
                          text="Left 16px", size=16, color=(255, 0, 0, 255))
    txt2 = ResponsiveText("10%", "20%", "80%", "50", 
                          text="Center 24px", size=24, color=(0, 255, 0, 255), align="center")
    txt3 = ResponsiveText("10%", "30%", "80%", "50", 
                          text="Right 32px", size=32, color=(0, 0, 255, 255), align="right")
    
    # Responsive size test (percentage of height 50px)
    # If height is 50px, and size is '50%', font size ~25px
    txt4 = ResponsiveText("10%", "50%", "80%", "50", 
                          text="Responsive Size 50%", size="50%", color=(0, 0, 0, 255), align="center")

    layer.add_child(txt1)
    layer.add_child(txt2)
    layer.add_child(txt3)
    layer.add_child(txt4)

    running = True
    while running:
        display_list = [layer.to_data()]
        win.render(display_list)
        
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
