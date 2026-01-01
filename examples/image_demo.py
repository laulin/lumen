import sys
import os
import sdl2
import sdl2.ext

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdl_gui import core
from sdl_gui.window.window import Window
from sdl_gui.layouts.vbox import VBox
from sdl_gui.layouts.hbox import HBox
from sdl_gui.layers.scrollable_layer import ScrollableLayer
from sdl_gui.primitives.image import Image
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.rectangle import Rectangle

# Constants for Styling
THEME_BG = (18, 18, 18, 255)  # Dark background, Alpha 255
THEME_CARD_BG = (30, 30, 30, 255)
THEME_TEXT_PRIMARY = (238, 238, 238, 255)
THEME_TEXT_SECONDARY = (170, 170, 170, 255)
THEME_ACCENT = (187, 134, 252, 255)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def create_image_card(image_path: str, title: str, subtitle: str) -> VBox:
    # Card Container
    card = VBox(x=0, y=0, width=300, height=320, padding=(0, 0, 0, 0), margin=(10, 10, 10, 10))
    
    # Image Area
    # Assuming Image primitive takes width/height
    img = Image(
        source=os.path.join(ASSETS_DIR, image_path),
        x=0, y=0, width=300, height=200,
        scale_mode="fit",
        margin=(0, 0, 10, 0)
    )
    
    # Text Content
    text_box = VBox(x=0, y=0, width="100%", height="auto", padding=(15, 15, 15, 15))
    
    title_text = ResponsiveText(
        x=0, y=0, width="100%", height="auto",
        text=title,
        size=20,
        color=THEME_TEXT_PRIMARY,
        margin=(0, 0, 5, 0)
    )
    
    sub_text = ResponsiveText(
        x=0, y=0, width="100%", height="auto",
        text=subtitle,
        size=14,
        color=THEME_TEXT_SECONDARY
    )
    
    # Assemble
    text_box.add_child(title_text)
    text_box.add_child(sub_text)
    
    card.add_child(img)
    card.add_child(text_box)
    
    return card

def main():
    width, height = 1024, 768
    win = Window("Lumen Gallery Showcase", width, height)
    
    # Gallery Data
    gallery_items = [
        ("arch.png", "Modern Architecture", "Minimalist concrete aesthetics"),
        ("nature.png", "Serene Landscape", "Misty mountains at sunrise"),
        ("cyber.png", "Neon City", "Cyberpunk futuristic vibes"),
        ("abstract.png", "Digital Dreams", "Vivid geometric abstractions"),
        ("nature.png", "Wilderness", "Untouched natural beauty"), 
        ("arch.png", "Structural Design", "Repeating patterns in concrete"),
    ]
    
    # --- Build UI Structure ---
    
    # Root Layer Structure: Background + Header + Scrollable
    # We construct the list directly because .to_data() is what the renderer expects.
    # But we use objects to build it.
    
    # 1. Background
    bg_rect = Rectangle(x=0, y=0, width=width, height=height, color=THEME_BG)
    
    # 2. Header
    header = VBox(x=0, y=0, width="100%", height=100, padding=(40, 30, 40, 30), margin=(0,0,0,0))
    header_title = ResponsiveText(
        x=0, y=0, width="100%", height="auto", 
        text="LUMEN GALLERY", size=32, color=THEME_ACCENT, margin=(0, 0, 5, 0)
    )
    header_subtitle = ResponsiveText(
        x=0, y=0, width="100%", height="auto",
        text="Showcasing high-performance rendering capabilities", size=16, color=THEME_TEXT_SECONDARY
    )
    header.add_child(header_title)
    header.add_child(header_subtitle)
    
    # 3. Scrollable Content
    scroll_layer = ScrollableLayer(x=0, y=100, width=width, height=height-100, content_height=1200, scroll_y=0)
    content_vbox = VBox(x=0, y=0, width=width, height=1200, padding=(40, 0, 40, 40))
    
    # Create Grid Rows
    chunk_size = 3
    for i in range(0, len(gallery_items), chunk_size):
        chunk = gallery_items[i:i + chunk_size]
        row = HBox(x=0, y=0, width="100%", height=350, margin=(0, 0, 20, 0)) # Fixed height for row
        
        for img_path, title, sub in chunk:
            card = create_image_card(img_path, title, sub)
            row.add_child(card)
            
        content_vbox.add_child(row)
        
    scroll_layer.add_child(content_vbox)

    display_list = [
        bg_rect.to_data(),
        header.to_data(),
        scroll_layer.to_data()
    ]

    running = True
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            if event.type == sdl2.SDL_KEYUP:
                 if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                      running = False
            
            # Scroll Handling
            if event.type == sdl2.SDL_MOUSEWHEEL:
                scroll_layer.scroll_y -= event.wheel.y * 20
                scroll_layer.scroll_y = max(0, min(scroll_layer.scroll_y, scroll_layer.content_height - scroll_layer.height))
                
                # Update display list
                # Since display_list includes dictionaries returned by to_data(), we need to update the dict
                # OR rebuild it. Rebuilding is safer to ensure state sync, but expensive?
                # For this demo, let's just update the specific key in the list item we know is the scroll layer.
                display_list[2][core.KEY_SCROLL_Y] = scroll_layer.scroll_y

        win.render(display_list)
        sdl2.SDL_Delay(10)

    sdl2.ext.quit()

if __name__ == "__main__":
    main()
