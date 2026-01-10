import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from sdl_gui.window.window import Window
from sdl_gui.layers.layer import Layer
from sdl_gui.layers.scrollable_layer import ScrollableLayer
from sdl_gui.layouts.vbox import VBox
from sdl_gui.layouts.hbox import HBox
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.primitives.responsive_text import ResponsiveText

def main():
    # Implicit parenting showcase
    with Window("Fake Wikipedia", 800, 600, debug=True) as window:
        
        # Main Layout Layer
        with Layer(0, 0, "100%", "100%") as main_layer:
            
            # Header
            with HBox(0, 0, "100%", 60, padding=10) as header:
                header.set_color(240, 240, 240, 255) # Light gray background
                
                # Logo Placeholder
                with HBox(0, 0, 150, "100%") as logo_box:
                    Rectangle(0, 0, 40, 40, color=(50, 50, 50, 255)).set_radius(20) # Icon
                    ResponsiveText(0, 0, "auto", "auto", text="Wikipedia", size=24, color=(0,0,0,255), margin=(5,0,0,10))

                # Search Bar
                with HBox(0, 0, 300, 40, margin=(0, 20, 0, 20)) as search_box:
                    search_box.set_color(255, 255, 255, 255).set_border_width(1).set_border_color(200, 200, 200, 255).set_radius(5)
                    ResponsiveText(10, 8, "auto", "auto", text="Search Wikipedia", color=(150, 150, 150, 255))
            
        # Content Area (Scrollable)
        # Calculate remaining height roughly or just use full and overlay? 
        # Layouts inside VBox would be better but let's assume we want a scrollable area below header.
        # Using VBox for main structure might be cleaner, let's try nesting.
        
        with ScrollableLayer(0, 60, "100%", "90%", content_height=1200) as content:
            
            with VBox(0, 0, "100%", "auto", padding=20) as article:
                
                # Title
                ResponsiveText(0, 0, "100%", "auto", text="Python (programming language)", size=32, margin=(0,0,20,0))
                
                # Horizontal Line
                Rectangle(0, 0, "100%", 1, color=(200, 200, 200, 255)).set_margin((0,0,20,0))
                
                # Two columns: Text and InfoBox
                with HBox(0, 0, "100%", "auto") as columns:
                    
                    # Main Text Column
                    with VBox(0, 0, "65%", "auto", padding=(0, 20, 0, 0)) as text_col:
                        
                        p1 = "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation."
                        ResponsiveText(0, 0, "100%", "auto", text=p1, size=16, margin=(0,0,15,0))
                        
                        p2 = "Python is dynamically-typed and garbage-collected. It supports multiple programming paradigms, including structured (particularly procedural), object-oriented and functional programming."
                        ResponsiveText(0, 0, "100%", "auto", text=p2, size=16, margin=(0,0,15,0))
                        
                        # Code example box
                        with VBox(0, 0, "100%", "auto", padding=15, margin=(10,0,20,0)) as code_block:
                            code_block.set_color(248, 248, 248, 255).set_border_width(1).set_border_color(220, 220, 220, 255).set_radius(3)
                            ResponsiveText(0, 0, "100%", "auto", text="def hello__world():\n    print('Hello, world!')", size=14, font="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")

                    # InfoBox Column
                    with VBox(0, 0, "30%", "auto", margin=(0,0,0,0)) as infobox:
                        infobox.set_color(250, 250, 250, 255).set_border_width(1).set_border_color(200, 200, 200, 255)
                        
                        # Infobox Header
                        with HBox(0, 0, "100%", 40, padding=10) as info_header:
                            info_header.set_color(200, 200, 255, 100) # Slight tint
                            ResponsiveText(0, 0, "100%", "auto", text="Python", size=18, align="center")
                            
                        # Image placeholder
                        Rectangle(20, 10, 100, 100, color=(50, 100, 200, 255)).set_margin((20, 20, 20, 20))
                        
                        # Details
                        with VBox(0, 0, "100%", "auto", padding=10) as details:
                            ResponsiveText(0, 0, "100%", "auto", text="Designed by: Guido van Rossum", size=12, margin=(0,0,5,0))
                            ResponsiveText(0, 0, "100%", "auto", text="First appeared: Feb 1991", size=12, margin=(0,0,5,0))

    # Render loop
    running = True
    while running:
        window.render(window.get_root_display_list())
        events = window.get_ui_events()
        for e in events:
            if e['type'] == 'quit':
                running = False
                
if __name__ == "__main__":
    main()
