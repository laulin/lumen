import sys
import os
import random
import sdl2.ext

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdl_gui.window.window import Window
from sdl_gui.layers.scrollable_layer import ScrollableLayer
from sdl_gui.layouts.vbox import VBox
from sdl_gui.layouts.hbox import HBox
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui import core

# --- DATA GENERATION ---
SUBREDDITS = [
    ("r/python", (50, 50, 200, 255)),
    ("r/programming", (0, 100, 0, 255)),
    ("r/rust", (200, 100, 0, 255)),
    ("r/linux", (50, 50, 50, 255)),
    ("r/technology", (0, 150, 200, 255)),
    ("r/gamedev", (150, 50, 150, 255))
]

USERS = ["dev_guru", "code_wizard", "linux_fan", "rust_evangelist", "pythonista", "ai_bot"]

POSTS = [
    ("Why Python is still #1 in 2025", "Python continues to dominate the AI and data science landscape. The release of Python 4.0 with JIT compilation as standard has silenced performance critics."),
    ("I rewrote my OS in Rust", "It took me 3 years but it's finally memory safe. The kernel is 50% smaller and boots in 0.1 seconds."),
    ("Vim vs Emacs: The Eternal War", "After 40 years, we still haven't decided. Here is why I think ed is logically superior to both."),
    ("SDL2 GUI from scratch", "Building a UI library is hard but rewarding. Layout algorithms are the trickiest part, especially properly handling text wrapping and recursion."),
    ("The end of JavaScript?", "WebAssembly is taking over. Is formatted text rendering in Canvas the future of web apps?"),
    ("My cat debugged my code", "I left my IDE open and my cat stepped on the keyboard. It fixed a race condition by adding a random sleep()."),
    ("Understanding AsyncIO", "A deep dive into event loops, coroutines and why you shouldn't block the main thread."),
    ("Linux Desktop Year 2026", "This time for sure. Gnome 50 changes everything by removing all UI elements for maximum minimalism.")
]

def create_post_card(index):
    """Create a Reddit-style post card."""
    sub_name, sub_color = random.choice(SUBREDDITS)
    user = random.choice(USERS)
    hours = random.randint(1, 23)
    title_txt, body_txt = random.choice(POSTS)
    upvotes = random.randint(0, 5000)
    comments = random.randint(0, 500)
    
    # Main Card Container (White background, shadow/border effect simulation)
    # Using 'color' property on VBox (newly supported)
    card = VBox(0, 0, "100%", "auto", padding=(0, 0, 0, 0), margin=(10, 10, 10, 10))
    card.extra[core.KEY_COLOR] = (255, 255, 255, 255) # White BG
    
    # --- META HEADER ---
    meta_box = HBox(0, 0, "100%", 30, padding=(10, 10, 5, 20))
    # Subreddit
    meta_box.add_child(ResponsiveText(0, 0, "auto", "100%", text=f"**{sub_name}**", size=12, color=sub_color, markup=True))
    # Dot
    meta_box.add_child(ResponsiveText(0, 0, 20, "100%", text="•", size=12, color=(150, 150, 150, 255), align="center"))
    # User
    meta_box.add_child(ResponsiveText(0, 0, "auto", "100%", text=f"Posted by u/{user}", size=12, color=(120, 120, 120, 255)))
    # Time
    meta_box.add_child(ResponsiveText(0, 0, "auto", "100%", text=f" {hours}h ago", size=12, color=(120, 120, 120, 255)))
    
    card.add_child(meta_box)
    
    # --- TITLE ---
    title_box = VBox(0, 0, "100%", "auto", padding=(10, 20, 5, 20))
    title_box.add_child(ResponsiveText(0, 0, "100%", "auto", text=f"**{title_txt}**", size=18, color=(20, 20, 20, 255), markup=True, wrap=True))
    card.add_child(title_box)
    
    # --- BODY ---
    body_box = VBox(0, 0, "100%", "auto", padding=(5, 20, 10, 20))
    body_box.add_child(ResponsiveText(0, 0, "100%", "auto", text=body_txt, size=14, color=(50, 50, 50, 255), wrap=True))
    card.add_child(body_box)
    
    # --- ACTION BAR ---
    action_box = HBox(0, 0, "100%", 35, padding=(10, 20, 10, 20))
    # Gray background for action bar? Optional.
    
    # Upvotes (Orangeish)
    action_box.add_child(ResponsiveText(0, 0, "auto", "100%", text="[▲]", size=14, color=(255, 69, 0, 255), markup=True))
    vote_str = f"{upvotes/1000:.1f}k" if upvotes > 1000 else str(upvotes)
    action_box.add_child(ResponsiveText(0, 0, "auto", "100%", text=f" {vote_str}", size=14, color=(20, 20, 20, 255)))
    action_box.add_child(ResponsiveText(0, 0, "auto", "100%", text=" [▼]", size=14, color=(148, 148, 255, 255), markup=True))
    
    # Spacing
    action_box.add_child(Rectangle(0, 0, 30, "100%", (0,0,0,0)))
    
    # Comments
    action_box.add_child(ResponsiveText(0, 0, "auto", "100%", text=f"[💬 {comments} Comments]", size=12, color=(100, 100, 100, 255), markup=True))
    
    card.add_child(action_box)
    
    return card

def main():
    win = Window("Optix Reddit Clone", 500, 800)
    
    # --- HEADER ---
    # Fixed at top
    header = HBox(0, 0, "100%", 50, padding=(0, 0, 0, 0))
    header.extra[core.KEY_COLOR] = (255, 255, 255, 255) # White BG
    
    logo_box = HBox(0, 0, "auto", "100%", padding=(15, 10, 15, 10))
    logo_box.add_child(ResponsiveText(0, 0, "auto", "auto", text="**reddit**", size=24, color=(255, 69, 0, 255), markup=True))
    logo_box.add_child(ResponsiveText(0, 0, 10, "auto", text=" ", size=24))
    logo_box.add_child(ResponsiveText(0, 0, "auto", "auto", text="demo", size=24, color=(0, 0, 0, 255)))
    header.add_child(logo_box)
    
    # Search bar simulation (Spacer + Rect)
    header.add_child(Rectangle(0, 0, 20, "100%", (0,0,0,0))) # Spacer
    search_bar = Rectangle(0, 0, 150, 30, (240, 240, 240, 255), margin=(10, 0, 10, 0))
    header.add_child(search_bar)
    
    # --- SCROLLABLE CONTENT ---
    # Starts at y=50
    scroll_layer = ScrollableLayer(0, 50, "100%", 750, id="feed", listen_events=[core.EVENT_SCROLL])
    
    content_vbox = VBox(0, 0, "100%", "auto")
    scroll_layer.add_child(content_vbox)
    
    # Add an empty spacer at top of feed to separate from header slightly more if needed
    content_vbox.add_child(Rectangle(0, 0, "100%", 10, (0,0,0,0)))

    # Initial Posts
    for i in range(10):
        content_vbox.add_child(create_post_card(i))

    running = True
    current_scroll_y = 0
    item_count = 10
    
    while running:
        scroll_layer.scroll_y = current_scroll_y
        
        display_list = [
            Rectangle(0, 0, "100%", "100%", (218, 224, 230, 255)).to_data(), # Global BG (Reddit Gray)
            scroll_layer.to_data(),
            header.to_data(), # Header on top
            Rectangle(0, 49, "100%", 1, (200, 200, 200, 255)).to_data() # Header Border
        ]
        
        win.render(display_list)
        
        ui_events = win.get_ui_events()
        for event in ui_events:
            if event["type"] == core.EVENT_QUIT:
                running = False
                
            elif event["type"] == core.EVENT_SCROLL:
                if event["target"] == "feed":
                    delta = event["delta"]
                    current_scroll_y -= delta * 40 # Sensitivity
                    if current_scroll_y < 0: current_scroll_y = 0
                    
                    approx_height = item_count * 200 # rough estimate per card
                    if current_scroll_y > approx_height - 1000:
                         print("Fetching more posts...")
                         for _ in range(5):
                             item_count += 1
                             content_vbox.add_child(create_post_card(item_count))
        
        sdl2.SDL_Delay(16)
        
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
