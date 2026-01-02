import sys
import os
import sdl2
import sdl2.ext

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdl_gui.window.window import Window
from sdl_gui.layouts.vbox import VBox
from sdl_gui.layouts.hbox import HBox
from sdl_gui.primitives.image import Image
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.rectangle import Rectangle

# Constants for Styling
THEME_BG = (18, 18, 18, 255)
THEME_TEXT_PRIMARY = (238, 238, 238, 255)
THEME_ACCENT = (187, 134, 252, 255)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def main():
    width, height = 1024, 768
    win = Window("Lumen Rounded Image Demo", width, height)
    
    # Check for assets
    image_path = os.path.join(ASSETS_DIR, "nature.png")
    if not os.path.exists(image_path):
        # Fallback to any file and hope it works or it will be empty
        print(f"Warning: {image_path} not found.")

    # 1. Background
    bg_rect = Rectangle(x=0, y=0, width=width, height=height, color=THEME_BG)
    
    # 2. Main Layout
    root_vbox = VBox(x=0, y=0, width="100%", height="100%", padding=(50, 50, 50, 50))
    
    title = ResponsiveText(
        x=0, y=0, width="100%", height="auto",
        text="Rounded Corners for Images",
        size=32, color=THEME_ACCENT, margin=(0, 0, 30, 0),
        align="center"
    )
    root_vbox.add_child(title)
    
    # 3. Row of Images with different radii
    row = HBox(x=0, y=0, width="100%", height=300, margin=(0, 0, 20, 0))
    
    radii = [0, 20, 50, 150]
    for r in radii:
        container = VBox(x=0, y=0, width=220, height=280, margin=(0, 10, 0, 10))
        
        img = Image(
            source=image_path,
            x=0, y=0, width=200, height=200,
            radius=r,
            scale_mode="fit",
            margin=(0, 0, 10, 0)
        )
        
        label = ResponsiveText(
            x=0, y=0, width="100%", height="auto",
            text=f"Radius: {r}px",
            size=16, color=THEME_TEXT_PRIMARY,
            align="center"
        )
        
        container.add_child(img)
        container.add_child(label)
        row.add_child(container)
        
    root_vbox.add_child(row)

    # 4. Large Image with extreme rounding
    large_img_container = VBox(x=0, y=0, width="100%", height=300)
    large_img = Image(
        source=image_path,
        x=0, y=0, width=400, height=250,
        radius=40,
        scale_mode="fit",
        id="large_rounded_img"
    )
    large_img_container.add_child(large_img)
    root_vbox.add_child(large_img_container)

    display_list = [
        bg_rect.to_data(),
        root_vbox.to_data()
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

        win.render(display_list)
        sdl2.SDL_Delay(16)

    sdl2.ext.quit()

if __name__ == "__main__":
    main()
