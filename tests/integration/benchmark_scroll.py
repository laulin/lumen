import sys
import os
import time
import sdl2.ext
import unittest

# Ensure src and examples are in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../examples")))

from sdl_gui.window.window import Window
from sdl_gui.layers.scrollable_layer import ScrollableLayer
from sdl_gui.layouts.vbox import VBox
from sdl_gui.layouts.hbox import HBox
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui import core
from infinite_scroll_demo import create_post_card

class TestBenchmarkScroll(unittest.TestCase):
    def test_benchmark_scroll(self):
        """Benchmark scrolling performance with complex UI."""
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        
        duration = 5.0 # Seconds
        width, height = 500, 800
        
        # Implicit API context usage
        with Window("Benchmark", width, height, renderer_flags=sdl2.SDL_RENDERER_SOFTWARE) as win:
            
            # --- HEADER (Simplified) ---
            with HBox(0, 0, "100%", 50, padding=(0, 15, 0, 15)) as header:
                header.set_background_color(26, 26, 27, 255)
                ResponsiveText(0, 0, "auto", "auto", text="**Benchmark**", size=20, color=(255, 255, 255, 255), markup=True, margin=(13, 0, 0, 0))

            # Content Layer: Pre-populate with items.
            with ScrollableLayer(0, 50, "100%", 750, id="feed") as scroll_layer:
                with VBox(0, 0, "100%", "auto", padding=(0, 10, 0, 10)) as content_vbox:
                    for i in range(50):
                       content_vbox.add_child(create_post_card(i))
                       
            
            running = True
            frame_count = 0
            start_time = time.time()
            
            target_scroll_y = 0.0
            current_scroll_y = 0.0
            
            print(f"\nStarting Scroll Benchmark for {duration} seconds...")
            
            while running:
                now = time.time()
                elapsed = now - start_time
                if elapsed >= duration:
                    break
                    
                # Auto Scroll Down
                target_scroll_y += 10 # Constant Scroll Speed
                
                # Smooth Scroll Logic (Lerp)
                diff = target_scroll_y - current_scroll_y
                if abs(diff) > 0.5:
                    current_scroll_y = target_scroll_y
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
                frame_count += 1
                sdl2.ext.get_events()
                
        avg_fps = frame_count / duration
        print(f"Benchmark Complete.")
        print(f"Total Frames: {frame_count}")
        print(f"Duration: {duration:.2f}s")
        print(f"Average FPS: {avg_fps:.2f}")

        sdl2.ext.quit()

if __name__ == "__main__":
    unittest.main()
