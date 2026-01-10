"""
Script de profiling pour infinite_scroll_demo.py
Exécute la démo pendant 3 secondes avec cProfile.
"""
import cProfile
import pstats
import io
import sys
import os
import time
import threading

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import random
import sdl2.ext
import sdl2

from sdl_gui.window.window import Window
from sdl_gui.layers.scrollable_layer import ScrollableLayer
from sdl_gui.layouts.vbox import VBox
from sdl_gui.layouts.hbox import HBox
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui import core

# --- DATA GENERATION (copié de infinite_scroll_demo.py) ---
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
    ("Why Python is still #1 in 2025", "Python continues to dominate the AI and data science landscape."),
    ("I rewrote my OS in Rust", "It took me 3 years but it's finally memory safe."),
    ("Vim vs Emacs: The Eternal War", "After 40 years, we still haven't decided."),
    ("SDL2 GUI from scratch", "Building a UI library is hard but rewarding."),
]


def create_post_card(index):
    """Create a Reddit-style post card."""
    sub_name, sub_color = random.choice(SUBREDDITS)
    user = random.choice(USERS)
    hours = random.randint(1, 23)
    title_txt, body_txt = random.choice(POSTS)
    upvotes = random.randint(0, 5000)
    comments = random.randint(0, 500)
    
    card_id = f"post_{index}"
    
    with VBox(0, 0, "100%", "auto", padding=(0, 0, 0, 0), margin=(10, 0, 10, 0), id=card_id) as card:
        card.set_background_color(35, 35, 35, 255)
        card.set_radius(10)
        card.set_border_width(1)
        card.set_border_color(60, 60, 60, 255)
        
        with HBox(0, 0, "100%", 30, padding=(10, 10, 5, 20), id=f"{card_id}_meta") as meta_box:
            ResponsiveText(0, 0, "auto", "100%", text=f"**{sub_name}**", size=12, color=sub_color, markup=True, id=f"{card_id}_sub")
            ResponsiveText(0, 0, 20, "100%", text="•", size=12, color=(129, 131, 132, 255), align="center", id=f"{card_id}_dot")
            ResponsiveText(0, 0, "auto", "100%", text=f"Posted by u/{user}", size=12, color=(129, 131, 132, 255), id=f"{card_id}_user")
            ResponsiveText(0, 0, "auto", "100%", text=f" {hours}h ago", size=12, color=(129, 131, 132, 255), id=f"{card_id}_time")
        
        with VBox(0, 0, "100%", "auto", padding=(10, 20, 5, 20), id=f"{card_id}_title_box") as title_box:
            ResponsiveText(0, 0, "100%", "auto", text=f"**{title_txt}**", size=18, color=(215, 218, 220, 255), markup=True, wrap=True, id=f"{card_id}_title")
        
        with VBox(0, 0, "100%", "auto", padding=(5, 20, 10, 20), id=f"{card_id}_body_box") as body_box:
            ResponsiveText(0, 0, "100%", "auto", text=body_txt, size=14, color=(215, 218, 220, 255), wrap=True, id=f"{card_id}_body")
        
        with HBox(0, 0, "100%", 35, padding=(10, 20, 10, 20), id=f"{card_id}_action_box") as action_box:
            ResponsiveText(0, 0, "auto", "100%", text="[▲]", size=14, color=(255, 69, 0, 255), markup=True, id=f"{card_id}_up")
            vote_str = f"{upvotes/1000:.1f}k" if upvotes > 1000 else str(upvotes)
            ResponsiveText(0, 0, "auto", "100%", text=f" {vote_str}", size=14, color=(215, 218, 220, 255), id=f"{card_id}_votes")
            ResponsiveText(0, 0, "auto", "100%", text=" [▼]", size=14, color=(113, 147, 255, 255), markup=True, id=f"{card_id}_down")
            Rectangle(0, 0, 30, "100%", color=(0,0,0,0), id=f"{card_id}_space")
            ResponsiveText(0, 0, "auto", "100%", text=f"[💬 {comments} Comments]", size=12, color=(129, 131, 132, 255), markup=True, id=f"{card_id}_comments")
    
    return card


def run_demo_for_duration(duration_seconds: float):
    """Run the infinite scroll demo for a specified duration."""
    start_time = time.time()
    
    with Window("Lumen Reddit Clone - Profiling", 500, 800, debug=False) as win:
        
        with FlexBox(0, 0, "100%", 50, padding=(0, 15, 0, 15), justify_content="space_between", align_items="center") as header:
            header.set_background_color(26, 26, 27, 255)
            
            with FlexBox(0, 0, "auto", "100%", align_items="center") as logo_box:
                with HBox(0, 0, 32, 32, margin=(0, 5, 0, 0)) as icon_box:
                    Rectangle(0, 0, 32, 32, color=(255, 69, 0, 255), radius=16)
                ResponsiveText(0, 0, "auto", "auto", text="**reddit**", size=20, color=(255, 255, 255, 255), markup=True)

            with FlexBox(0, 0, "auto", 36, margin=(0, 20, 0, 20), align_items="center") as search_box:
                search_box.set_flex_grow(1)
                search_box.set_background_color(39, 40, 41, 255)
                search_box.set_radius(18)
                ResponsiveText(0, 0, "auto", "auto", text="🔍", size=14, color=(129, 131, 132, 255), margin=(0, 0, 0, 10))
                ResponsiveText(0, 0, "auto", "auto", text="Search", size=14, color=(129, 131, 132, 255), margin=(0, 0, 0, 5))

            with FlexBox(0, 0, "auto", "100%", align_items="center") as actions_box:
                with FlexBox(0, 0, 70, 32, margin=(0, 5, 0, 0), justify_content="center", align_items="center") as login_btn:
                    login_btn.set_border_width(1)
                    login_btn.set_border_color(215, 218, 220, 255)
                    login_btn.set_radius(16)
                    ResponsiveText(0, 0, "auto", "auto", text="Log In", size=12, color=(215, 218, 220, 255), align="center")

                with FlexBox(0, 0, 70, 32, margin=(0, 0, 0, 5), justify_content="center", align_items="center") as signup_btn:
                    signup_btn.set_background_color(215, 218, 220, 255)
                    signup_btn.set_radius(16)
                    ResponsiveText(0, 0, "auto", "auto", text="Sign Up", size=12, color=(26, 26, 27, 255), align="center")

        with ScrollableLayer(0, 50, "100%", 750, id="feed", listen_events=[core.EVENT_SCROLL]) as scroll_layer:
            with VBox(0, 0, "100%", "auto", padding=(0, 10, 0, 10)) as content_vbox:
                for i in range(10):
                   create_post_card(i)

        running = True
        target_scroll_y = 0.0
        current_scroll_y = 0.0
        item_count = 10
        frame_count = 0
        
        # Simulating scroll activity for profiling
        scroll_direction = 1
        
        while running:
            elapsed = time.time() - start_time
            if elapsed >= duration_seconds:
                running = False
                continue
            
            # Simulate smooth scrolling for profiling
            if frame_count % 60 == 0:
                scroll_direction = -scroll_direction
            target_scroll_y += scroll_direction * 5
            if target_scroll_y < 0:
                target_scroll_y = 0
            
            diff = target_scroll_y - current_scroll_y
            if abs(diff) > 0.5:
                current_scroll_y += diff * 0.1
            else:
                current_scroll_y = target_scroll_y

            scroll_layer.scroll_y = int(current_scroll_y)
            
            display_list = [
                Rectangle(0, 0, "100%", "100%", color=(3, 3, 3, 255)).to_data(),
                scroll_layer.to_data(),
                header.to_data(),
                Rectangle(0, 49, "100%", 1, color=(52, 53, 54, 255)).to_data()
            ]
            
            win.render(display_list)
            
            ui_events = win.get_ui_events()
            for event in ui_events:
                if event["type"] == core.EVENT_QUIT:
                    running = False

            frame_count += 1
            sdl2.SDL_Delay(8)
        
        print(f"Profiling complete: {frame_count} frames in {elapsed:.2f}s ({frame_count/elapsed:.1f} FPS)")
    
    sdl2.ext.quit()


def main():
    """Main entry point for profiling."""
    print("=" * 60)
    print("Profiling infinite_scroll_demo.py for 3 seconds...")
    print("=" * 60)
    
    # Create profiler
    profiler = cProfile.Profile()
    
    # Run profiling
    profiler.enable()
    run_demo_for_duration(3.0)
    profiler.disable()
    
    # Generate stats
    print("\n" + "=" * 60)
    print("PROFILING RESULTS - TOP 50 by cumulative time")
    print("=" * 60)
    
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(50)
    print(stream.getvalue())
    
    # Also print by total time
    print("\n" + "=" * 60)
    print("PROFILING RESULTS - TOP 30 by total time (self)")
    print("=" * 60)
    
    stream2 = io.StringIO()
    stats2 = pstats.Stats(profiler, stream=stream2)
    stats2.strip_dirs()
    stats2.sort_stats('tottime')
    stats2.print_stats(30)
    print(stream2.getvalue())
    
    # Print callers for key functions
    print("\n" + "=" * 60)
    print("CALLERS for render-related functions")
    print("=" * 60)
    
    stream3 = io.StringIO()
    stats3 = pstats.Stats(profiler, stream=stream3)
    stats3.strip_dirs()
    stats3.print_callers('render', 20)
    print(stream3.getvalue())


if __name__ == "__main__":
    main()
