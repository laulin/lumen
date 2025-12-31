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
    
    # Main Card Container (Dark Theme)
    with VBox(0, 0, "100%", "auto", padding=(0, 0, 0, 0), margin=(10, 0, 10, 0)) as card:
        card.set_background_color(35, 35, 35, 255) # Neutral Grey
        card.set_radius(10)
        card.set_border_width(1)
        card.set_border_color(60, 60, 60, 255)
        
        # --- META HEADER ---
        with HBox(0, 0, "100%", 30, padding=(10, 10, 5, 20)) as meta_box:
            # Subreddit
            ResponsiveText(0, 0, "auto", "100%", text=f"**{sub_name}**", size=12, color=sub_color, markup=True)
            # Dot
            ResponsiveText(0, 0, 20, "100%", text="•", size=12, color=(129, 131, 132, 255), align="center")
            # User
            ResponsiveText(0, 0, "auto", "100%", text=f"Posted by u/{user}", size=12, color=(129, 131, 132, 255))
            # Time
            ResponsiveText(0, 0, "auto", "100%", text=f" {hours}h ago", size=12, color=(129, 131, 132, 255))
        
        # --- TITLE ---
        with VBox(0, 0, "100%", "auto", padding=(10, 20, 5, 20)) as title_box:
            # Title Color: Light Gray D7DADC
            ResponsiveText(0, 0, "100%", "auto", text=f"**{title_txt}**", size=18, color=(215, 218, 220, 255), markup=True, wrap=True)
        
        # --- BODY ---
        with VBox(0, 0, "100%", "auto", padding=(5, 20, 10, 20)) as body_box:
            # Body Color: Slightly darker gray
            ResponsiveText(0, 0, "100%", "auto", text=body_txt, size=14, color=(215, 218, 220, 255), wrap=True)
        
        # --- ACTION BAR ---
        with HBox(0, 0, "100%", 35, padding=(10, 20, 10, 20)) as action_box:
            
            # Upvotes (Orangeish)
            ResponsiveText(0, 0, "auto", "100%", text="[▲]", size=14, color=(255, 69, 0, 255), markup=True)
            vote_str = f"{upvotes/1000:.1f}k" if upvotes > 1000 else str(upvotes)
            # Text Color
            ResponsiveText(0, 0, "auto", "100%", text=f" {vote_str}", size=14, color=(215, 218, 220, 255))
            ResponsiveText(0, 0, "auto", "100%", text=" [▼]", size=14, color=(113, 147, 255, 255), markup=True)
            
            # Spacing
            Rectangle(0, 0, 30, "100%", color=(0,0,0,0))
            
            # Comments
            ResponsiveText(0, 0, "auto", "100%", text=f"[💬 {comments} Comments]", size=12, color=(129, 131, 132, 255), markup=True)
    
    return card

def main():
    # Implicit API context usage
    with Window("Optix Reddit Clone", 500, 800) as win:
        
        # --- HEADER ---
        with HBox(0, 0, "100%", 50, padding=(0, 15, 0, 15)) as header:
            header.set_background_color(26, 26, 27, 255)
            
            # 1. Logo Section
            with HBox(0, 0, "auto", "100%") as logo_box:
                # Icon Circle
                with HBox(0, 0, 32, 32, margin=(9, 5, 9, 0)) as icon_box:
                    Rectangle(0, 0, 32, 32, color=(255, 69, 0, 255), radius=16)
                
                ResponsiveText(0, 0, "auto", "auto", text="**reddit**", size=20, color=(255, 255, 255, 255), markup=True, margin=(13, 0, 0, 0))

            # 2. Search Bar
            # Flexible spacer
            # Reduced width to fit
            with HBox(0, 0, 120, 36, margin=(7, 10, 7, 10)) as search_box:
                search_box.set_background_color(39, 40, 41, 255)
                search_box.set_radius(18)
                
                # Search Icon & Placeholder
                ResponsiveText(0, 0, "auto", "auto", text="🔍", size=14, color=(129, 131, 132, 255), margin=(8, 0, 0, 10))
                ResponsiveText(0, 0, "auto", "auto", text="Search", size=14, color=(129, 131, 132, 255), margin=(9, 0, 0, 5))

            # 3. Actions (Right side)
            # Login / Signup
            with HBox(0, 0, "auto", "100%") as actions_box:
                
                # Log In Button
                with HBox(0, 0, 70, 32, margin=(9, 5, 9, 0)) as login_btn:
                    login_btn.set_border_width(1)
                    login_btn.set_border_color(215, 218, 220, 255)
                    login_btn.set_radius(16)
                    ResponsiveText(0, 0, 70, "auto", text="Log In", size=12, color=(215, 218, 220, 255), align="center", margin=(9, 0, 0, 0))

                # Sign Up Button
                with HBox(0, 0, 70, 32, margin=(9, 0, 9, 5)) as signup_btn:
                    signup_btn.set_background_color(215, 218, 220, 255)
                    signup_btn.set_radius(16)
                    # Text inside needs to be black
                    ResponsiveText(0, 0, 70, "auto", text="Sign Up", size=12, color=(26, 26, 27, 255), align="center", margin=(9, 0, 0, 0))

        # --- CONTENT LAYER ---
        with ScrollableLayer(0, 50, "100%", 750, id="feed", listen_events=[core.EVENT_SCROLL]) as scroll_layer:
            with VBox(0, 0, "100%", "auto", padding=(0, 10, 0, 10)) as content_vbox:
                # Initial Posts
                for i in range(10):
                   create_post_card(i) # Implicitly adds to content_vbox

        # Render loop
        running = True
        current_scroll_y = 0
        item_count = 10
        
        while running:
            scroll_layer.scroll_y = current_scroll_y
            
            # Manual Display List Assembly (for stacking Layers)
            # We construct the list explicitly to control Z-order (Painter's Algorithm)
            display_list = [
                Rectangle(0, 0, "100%", "100%", color=(3, 3, 3, 255)).to_data(), # Global BG (Deep Black)
                scroll_layer.to_data(), # Content first
                header.to_data(), # Header on top
                Rectangle(0, 49, "100%", 1, color=(52, 53, 54, 255)).to_data() # Header Border
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
                        
                        approx_height = item_count * 200 
                        if current_scroll_y > approx_height - 1000:
                             for _ in range(5):
                                 item_count += 1
                                 create_post_card(item_count) 
                                 content_vbox.add_child(create_post_card(item_count))

        
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
