import os
import threading
import time
import unittest
import sdl2

from sdl_gui import core
from sdl_gui.window.window import Window
from sdl_gui.primitives.vector_graphics import VectorGraphics
from sdl_gui.debug.client import DebugClient

class TestVectorGraphicsDebug(unittest.TestCase):
    def setUp(self):
        # Use dummy driver to avoid opening actual windows during CI/Testing
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    def run_vector_test(self, setup_fn, validation_fn):
        """
        Helper to run a vector graphics test.
        
        Args:
            setup_fn: Function(window) -> None. Called to add primitives to window.
            validation_fn: Function(client, results_dict) -> None. Called in client thread.
        """
        # 1. Setup Window & Content
        window = Window("Test Vector", 200, 200, debug=True, renderer_flags=sdl2.SDL_RENDERER_SOFTWARE)
        
        setup_fn(window)
        
        # Shared state for assertions
        test_results = {"errors": []}
        
        def client_thread_func():
            try:
                # Give server time to start
                time.sleep(0.5)
                
                client = DebugClient()
                client.connect()
                
                validation_fn(client, test_results)
                
                # Done
                client.quit()
                client.close()
                
            except Exception as e:
                test_results["errors"].append(f"Client exception: {e}")

        # 2. Start Test Thread
        t = threading.Thread(target=client_thread_func)
        t.start()
        
        # 3. specific Run Loop for Test
        running = True
        while running:
            # Render
            display_list = window.get_root_display_list()
            window.render(display_list)
            
            # Process Events
            events = window.get_ui_events()
            for event in events:
                if event.get("type") == core.EVENT_QUIT:
                    running = False
            
            # Check if thread is still alive
            if not t.is_alive():
                running = False

            # Small sleep to yield CPU
            time.sleep(0.01)
            
        t.join()
        
        # Cleanup Debug Server to release port
        if window.debug_server:
            window.debug_server.stop()
            # Give it a moment to close socket
            time.sleep(1.2)
        
        # 4. Assertions
        if test_results["errors"]:
             self.fail("\n".join(test_results["errors"]))

    def test_line_to_rendering(self):
        """Test that line_to correctly renders a line using pixel inspection."""
        
        def setup(window):
            vg = VectorGraphics(0, 0, 200, 200, id="vg_line")
            vg.move_to(10, 10).stroke((255, 0, 0, 255), width=1).line_to(50, 10)
            window.add_child(vg)
            
        def validate(client, results):
            # Check pixel on the line (e.g., 30, 10) -> Red
            resp = client.get_pixel(30, 10)
            if resp.get("status") != "ok":
                results["errors"].append(f"Failed to get pixel: {resp}")
            else:
                color = tuple(resp.get("data"))
                if color != (255, 0, 0, 255):
                    results["errors"].append(f"Pixel at (30,10) mismatch. Expected (255,0,0,255), got {color}")
            
            # Check pixel OFF the line (e.g., 30, 20) -> Not Red
            resp = client.get_pixel(30, 20)
            if resp.get("status") == "ok":
                color = tuple(resp.get("data"))
                if color == (255, 0, 0, 255):
                     results["errors"].append(f"Pixel at (30,20) should NOT be red, got {color}")

        self.run_vector_test(setup, validate)

    def test_curve_to_rendering(self):
        """Test that curve_to renders something approximate to a bezier curve."""
        
        def setup(window):
            vg = VectorGraphics(0, 0, 200, 200, id="vg_curve")
            # Quadratic-like Cubic Bezier: start(10,10), control(50, 100) & (50, 100), end(100, 10)
            # This should dip down towards y=100 in the middle x=55
            vg.move_to(10, 10)
            vg.stroke((0, 255, 0, 255), width=1) # Green
            vg.curve_to(50, 100, 50, 100, 100, 10)
            window.add_child(vg)
            
        def validate(client, results):
            # Midpoint approximation of cubic bezier (10,10)->(50,100)->(50,100)->(100,10)
            # t=0.5
            # x = 0.125*10 + 0.375*50 + 0.375*50 + 0.125*100 = 51.25
            # y = 0.125*10 + 0.375*100 + 0.375*100 + 0.125*10 = 77.5
            
            target_x, target_y = 51, 77
            resp = client.get_pixel(target_x, target_y)
            
            found_green = False
            if resp.get("status") == "ok":
                 color = tuple(resp.get("data"))
                 if color == (0, 255, 0, 255):
                     found_green = True
            
            # If strict point failed, maybe check neighbor (simple tolerance)
            if not found_green:
                # check neighbors
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx==0 and dy==0: continue
                        resp = client.get_pixel(target_x+dx, target_y+dy)
                        if resp.get("status") == "ok":
                            if tuple(resp.get("data")) == (0, 255, 0, 255):
                                found_green = True
                                break
                    if found_green: break
            
            if not found_green:
                results["errors"].append(f"Failed to find GREEN pixel at or near ({target_x}, {target_y}) for curve.")

            # Check logic OFF the curve (e.g. 52, 10 - top, where straight line would be)
            resp = client.get_pixel(52, 10)
            if resp.get("status") == "ok":
                 color = tuple(resp.get("data"))
                 if color == (0, 255, 0, 255):
                     results["errors"].append(f"Pixel at (52, 10) should NOT be green (should be empty space inside curve arch)")

        self.run_vector_test(setup, validate)

    def test_rect_rendering(self):
        """Test that rect commands handle fill and stroke correctly."""
        
        def setup(window):
            vg = VectorGraphics(0, 0, 200, 200, id="vg_rect")
            
            # Rect 1: Filled Blue, No Stroke
            vg.stroke((255,255,255), width=0) # Disable stroke
            vg.fill((0, 0, 255, 255)) # Blue Fill
            vg.rect(10, 10, 30, 30) # Rect at (10,10) size 30x30. Center approx (25, 25)
            
            # Rect 2: Stroked White, No Fill
            vg.fill(()) 
            # Note: renderer logic for fill(()) -> len=0 -> c=[] -> if c: False -> fill_color=None. This is expected behavior.
            
            vg.stroke((255, 255, 255, 255), width=2)
            vg.rect(50, 10, 30, 30) # Rect at (50,10). Center (65, 25).
            
            window.add_child(vg)
            
        def validate(client, results):
            # Check Rect 1 Center (Blue)
            resp = client.get_pixel(25, 25)
            if resp.get("status") == "ok":
                color = tuple(resp.get("data"))
                if color != (0, 0, 255, 255):
                    results["errors"].append(f"Rect 1 center should be Blue (0,0,255,255), got {color}")
            else:
                results["errors"].append(f"Failed to get pixel for Rect 1: {resp}")

            # Check Rect 2 Center (NOT Blue, NOT White)
            resp = client.get_pixel(65, 25)
            if resp.get("status") == "ok":
                color = tuple(resp.get("data"))
                if color == (0, 0, 255, 255):
                     results["errors"].append(f"Rect 2 center should NOT be Blue, got {color} (Fill not cleared?)")
                if color == (255, 255, 255, 255):
                     results["errors"].append(f"Rect 2 center should NOT be White, got {color} (Filled with stroke color?)")

            # Check Rect 2 Border (White)
            # (50, 10) is top-left corner.
            resp = client.get_pixel(50, 10)
            if resp.get("status") == "ok":
                 color = tuple(resp.get("data"))
                 if color != (255, 255, 255, 255):
                     results["errors"].append(f"Rect 2 border at (50,10) should be White, got {color}")

        self.run_vector_test(setup, validate)

if __name__ == '__main__':
    unittest.main()
