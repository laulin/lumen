import sys
import os
import sdl2.ext

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdl_gui.window.window import Window
from sdl_gui.layers.layer import Layer
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.layouts.vbox import VBox
from sdl_gui.layouts.hbox import HBox

def main():
    # Increase resolution for better look
    win = Window("Modern Web Layout Demo", 1024, 768)
    win.show()

    # Root Layer (Background)
    root = Layer(0, 0, "100%", "100%")
    
    # Background (White page)
    bg = Rectangle(0, 0, "100%", "100%", color=(255, 255, 255, 255))
    root.add_child(bg)
    
    # --- Header ---
    # Header Height = 80px
    header_bg = Rectangle(0, 0, "100%", 80, color=(33, 33, 33, 255)) # Dark header
    
    header_layout = HBox(0, 0, "100%", 80, padding=(0, 20, 0, 20))
    
    # Logo
    logo = ResponsiveText(0, 0, "20%", "100%", text="Optix", size=32, color=(255, 255, 255, 255), align="center")
    
    # Nav Links
    nav_box = HBox(0, 0, "60%", "100%")
    nav1 = ResponsiveText(0, 0, "25%", "100%", text="Home", size=18, color=(200, 200, 200, 255), align="center")
    nav2 = ResponsiveText(0, 0, "25%", "100%", text="Features", size=18, color=(200, 200, 200, 255), align="center")
    nav3 = ResponsiveText(0, 0, "25%", "100%", text="Pricing", size=18, color=(200, 200, 200, 255), align="center")
    nav4 = ResponsiveText(0, 0, "25%", "100%", text="Contact", size=18, color=(200, 200, 200, 255), align="center")
    
    nav_box.add_child(nav1)
    nav_box.add_child(nav2)
    nav_box.add_child(nav3)
    nav_box.add_child(nav4)
    
    header_layout.add_child(logo)
    header_layout.add_child(nav_box)
    
    # --- Main Content ---
    # Start at Y=80 (use int)
    main_layout = VBox(0, 80, "100%", "100%", padding=(20, 0, 0, 0))
    
    # Hero Section
    # Height 300px
    hero_section = VBox(0, 0, "100%", 300, padding=(40, 40, 40, 40))
    
    headline = ResponsiveText(0, 0, "100%", 80, text="Build Faster GUIs", size=48, color=(33, 33, 33, 255), align="center")
    subtitle = ResponsiveText(0, 0, "100%", 40, text="Responsive, native, and easy to use.", size=24, color=(100, 100, 100, 255), align="center")
    
    hero_section.add_child(headline)
    hero_section.add_child(subtitle)
    
    # Features Grid
    grid = HBox(0, 0, "100%", 300, padding=(20, 20, 20, 20))
    
    # Feature 1
    col1 = VBox(0, 0, "30%", "100%", margin=(0, 10, 0, 10))
    c1_title = ResponsiveText(0, 0, "100%", 40, text="Fast", size=20, color=(0, 120, 200, 255), align="center")
    c1_desc = ResponsiveText(0, 0, "100%", 60, text="Optimized rendering.", size=16, color=(60, 60, 60, 255), align="center")
    
    # To simulate card bg, we'd need a rect, but VBox children stack.
    # workaround: just text for now.
    col1.add_child(c1_title)
    col1.add_child(c1_desc)

    # Feature 2
    col2 = VBox(0, 0, "30%", "100%", margin=(0, 10, 0, 10))
    c2_title = ResponsiveText(0, 0, "100%", 40, text="Flexible", size=20, color=(0, 180, 100, 255), align="center")
    c2_desc = ResponsiveText(0, 0, "100%", 60, text="Nested layouts.", size=16, color=(60, 60, 60, 255), align="center")
    col2.add_child(c2_title)
    col2.add_child(c2_desc)
    
    # Feature 3
    col3 = VBox(0, 0, "30%", "100%", margin=(0, 10, 0, 10))
    c3_title = ResponsiveText(0, 0, "100%", 40, text="Native", size=20, color=(200, 80, 0, 255), align="center")
    c3_desc = ResponsiveText(0, 0, "100%", 60, text="SDL2 power.", size=16, color=(60, 60, 60, 255), align="center")
    col3.add_child(c3_title)
    col3.add_child(c3_desc)
    
    grid.add_child(col1)
    grid.add_child(col2)
    grid.add_child(col3)
    
    main_layout.add_child(hero_section)
    main_layout.add_child(grid)
    
    root.add_child(header_bg)     # Absolute pos 0,0
    root.add_child(header_layout) # Absolute pos 0,0
    root.add_child(main_layout)   # Absolute pos 0,80

    running = True
    while running:
        display_list = [root.to_data()]
        win.render(display_list)
        
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
