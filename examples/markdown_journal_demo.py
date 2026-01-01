import sys
import os
import sdl2.ext

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdl_gui.window.window import Window
from sdl_gui.layouts.vbox import VBox
from sdl_gui.layouts.hbox import HBox
from sdl_gui.layers.layer import Layer
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui import core

# Font Configuration
SERIF_FONT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"

def main():
    # Initialize Window
    win = Window("The Python Daily", 900, 700)
    
    # Root Layer (Z-ordering)
    background_layer = Layer(0, 0, "100%", "100%")
    # White Paper Background
    background_layer.add_child(Rectangle(0, 0, "100%", "100%", color=(250, 250, 250, 255)))
    
    content_layer = VBox(0, 0, "100%", "100%", padding="20px")
    
    # --- HEADER ---
    # --- HEADER ---
    # Title
    header_box = VBox(0, 0, "100%", "auto", margin=(0, 0, 10, 0))
    
    title = ResponsiveText(0, 0, "100%", "auto", 
        text="**THE PYTHON DAILY**", 
        size=56, 
        color=(20, 20, 20, 255), 
        font=SERIF_BOLD, 
        align="center", 
        markup=True
    )
    
    # Date Line with Separators
    # Top Line
    header_box.add_child(Rectangle(0, 0, "100%", 2, color=(50, 50, 50, 255), margin=(0, 0, 5, 0)))
    
    date_line = ResponsiveText(0, 0, "100%", "auto", 
        text="**Vol. 1**   |   New York, [December 30, 2025]{#444444}   |   Price: [Free]{#006600}", 
        size=16, 
        color=(20, 20, 20, 255), 
        font=SERIF_FONT,
        align="center", 
        markup=True
    )
    header_box.add_child(title)
    header_box.add_child(date_line)
    
    # Bottom Line
    header_box.add_child(Rectangle(0, 0, "100%", 1, color=(50, 50, 50, 255), margin=(5, 0, 20, 0)))
    
    
    # --- MAIN CONTENT (3 Columns) ---
    columns_layout = HBox(0, 0, "100%", "auto")
    
    # Column 1 (Left Sidebar)
    col1 = VBox(0, 0, "25%", "auto", margin=(0, 20, 0, 0)) 
    col1.add_child(ResponsiveText(0, 0, "100%", "auto", text="**LOCAL NEWS**", size=18, color=(100, 0, 0, 255), font=SERIF_BOLD, markup=True))
    col1.add_child(Rectangle(0, 0, "100%", 1, color=(200, 200, 200, 255), margin=(2, 0, 10, 0)))
    
    col1.add_child(ResponsiveText(0, 0, "100%", "auto", 
        text="**Library Update**\n\n"
             "The new [SDL GUI]{#000088} library now supports full [Markdown]{#AA00AA} syntax.\n\n"
             "Citizens report high satisfaction with the new **white paper** look.\n\n"
             "[Read full story...](story1)",
        size=14, color=(10, 10, 10, 255), font=SERIF_FONT, markup=True, wrap=True
    ))

    # Column 2 (Main Story)
    col2 = VBox(0, 0, "45%", "auto", margin=(0, 20, 0, 20))
    # Main Header
    col2.add_child(ResponsiveText(0, 0, "100%", "auto", text="**MARKDOWN REVOLUTION**", size=32, color=(10, 10, 10, 255), font=SERIF_BOLD, align="center", markup=True))
    
    col2.add_child(ResponsiveText(0, 0, "100%", "auto", 
        text="**By A. Developer**\n\n"
             "   It was a sunny afternoon when the decision was made. No more HTML tags. "
             "The people wanted **simplicity**. They wanted `**bold**` asterisks and `[]` brackets.\n\n"
             "   \"It's just cleaner,\" said one expert. \"Now we can write articles like this one easily.\"\n\n"
             "   The new system supports:\n"
             "   - **Bold text** for emphasis.\n"
             "   - [Colored text]{#880000} for style.\n"
             "   - [Interactive Links](link_target) for navigation.\n\n"
             "   This page itself demonstrates the power of the engine.", 
        size=18, color=(10, 10, 10, 255), font=SERIF_FONT, markup=True, wrap=True
    ))

    # Column 3 (Right Sidebar)
    col3 = VBox(0, 0, "25%", "auto", margin=(0, 0, 0, 10))
    col3.add_child(ResponsiveText(0, 0, "100%", "auto", text="**MARKET WATCH**", size=18, color=(0, 80, 0, 255), font=SERIF_BOLD, markup=True))
    col3.add_child(Rectangle(0, 0, "100%", 1, color=(200, 200, 200, 255), margin=(2, 0, 10, 0)))
    
    col3.add_child(ResponsiveText(0, 0, "100%", "auto", 
        text="**Python**: [UP]{#008800} 2.5%\n"
             "**C++**: [STABLE]{#000088}\n"
             "**Rust**: [UP]{#008800} 5.0%\n\n"
             "**Weather**:\n"
             "[Sunny]{#FFA500} 25C\n\n"
             "[Ads](ads):\n"
             "Buy more RAM!", 
        size=14, color=(10, 10, 10, 255), font=SERIF_FONT, markup=True, wrap=True
    ))

    columns_layout.add_child(col1)
    columns_layout.add_child(col2)
    columns_layout.add_child(col3)

    # Assemble Page
    content_layer.add_child(header_box)
    content_layer.add_child(columns_layout)
    
    # Root Structure
    # Since VBox writes on top of previous siblings in display list order (if they overlap?), 
    # but here we want layering.
    # We can just put them in a list. Layers are primitives.
    # Window renders list order.
    
    root_elements = [background_layer.to_data(), content_layer.to_data()]

    # Initial Render
    win.show()
    
    running = True

    while running:
        win.render(root_elements)
        
        events = win.get_ui_events()
        for event in events:
            if event["type"] == core.EVENT_LINK_CLICK:
                print(f"User clicked a link: {event['target']}")
            elif event["type"] == core.EVENT_QUIT:
                running = False
        
        # Poll SDL events for quit
        # Note: Window.get_ui_events() already drained events.
        # But just in case any residuals:
        for event in sdl2.ext.get_events():
             pass # Already handled or consumed.
        
        win.window.refresh()
        sdl2.SDL_Delay(8)

if __name__ == "__main__":
    main()
