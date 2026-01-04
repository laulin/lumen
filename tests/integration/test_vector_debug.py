import os
import threading
import time
import unittest
import sdl2

from sdl_gui import core
from sdl_gui.window.window import Window
from sdl_gui.primitives.vector_graphics import VectorGraphics
from sdl_gui.layers.layer import Layer
from sdl_gui.layers.scrollable_layer import ScrollableLayer
from sdl_gui.layouts.vbox import VBox
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

    def test_relative_layer_positioning(self):
        """Test that VG inside a Layer is rendered at layer_pos + vg_pos."""
        def setup(window):
            # Layer at (50, 50)
            layer = Layer(50, 50, 100, 100)
            
            # VG at (10, 10) inside Layer
            vg = VectorGraphics(10, 10, 50, 50, id="vg_layer_pos")
            # Draw rect at (0,0) in VG coords
            vg.fill((0, 255, 0, 255))
            vg.stroke((0, 0, 0, 0), width=0)
            vg.rect(0, 0, 20, 20)
            
            layer.add_child(vg)
            window.add_child(layer)

        def validate(client, results):
            # Target Pixel Global:
            # Layer X (50) + VG X (10) + Rect X (0) = 60
            # Layer Y (50) + VG Y (10) + Rect Y (0) = 60
            # Center of rect (0,0,20,20) relative to VG is (10,10)
            # So Global Check at (60+10, 60+10) = (70, 70)
            
            resp = client.get_pixel(70, 70)
            if resp.get("status") == "ok":
                color = tuple(resp.get("data"))
                if color != (0, 255, 0, 255):
                    results["errors"].append(f"Pixel at (70,70) should be Green (Layer Pos), got {color}")
            else:
                results["errors"].append(f"Failed to get pixel: {resp}")

        self.run_vector_test(setup, validate)

    def test_relative_primitive_positioning(self):
        """Test that VG inside a VBox with padding is offset correctly."""
        def setup(window):
            # VBox at (0,0) with Padding 20
            vbox = VBox(0, 0, 200, 200)
            vbox.set_padding(20)
            
            # VG inside VBox
            # In simple layout, VBox should position child at (padding, padding) + child margin (0)
            vg = VectorGraphics(0, 0, 50, 50, id="vg_vbox_pos")
            vg.fill((0, 0, 255, 255))
            vg.stroke((0,0,0,0), width=0)
            vg.rect(0, 0, 20, 20)
            
            vbox.add_child(vg)
            window.add_child(vbox)

        def validate(client, results):
            # Target Pixel Global:
            # VBox (0,0) + Padding (20,20) = VG Origin (20,20)
            # Rect at (0,0) in VG. Center (10,10).
            # Global: (20+10, 20+10) = (30, 30)
            
            resp = client.get_pixel(30, 30)
            if resp.get("status") == "ok":
                color = tuple(resp.get("data"))
                if color != (0, 0, 255, 255):
                     results["errors"].append(f"Pixel at (30,30) should be Blue (VBox Padding), got {color}")
            else:
                 results["errors"].append(f"Failed to get pixel: {resp}")

        self.run_vector_test(setup, validate)
        
    def test_clipping_behavior(self):
        """Test that VG content outside parent bounds is clipped."""
        def setup(window):
            # ScrollableLayer acts as a clipping container.
            # Pos (50, 50), Size (100, 100). Global Clip Region: (50,50,100,100) -> ends at (150,150)
            clip_layer = ScrollableLayer(50, 50, 100, 100)
            
            # Large VG inside, at (0,0) relative to layer (so 50,50 global)
            vg = VectorGraphics(0, 0, 200, 200, id="vg_clipped")
            vg.fill((255, 0, 0, 255)) # Red
            vg.stroke((0,0,0,0), width=0)
            # Draw rect from (0,0) to (200,50) -> a long horizontal bar
            vg.rect(0, 0, 200, 50)
            
            clip_layer.add_child(vg)
            window.add_child(clip_layer)
        
        def validate(client, results):
            # 1. Inside Clip Region
            # VG Start (50,50). Rect covers (50,50) to (250, 100).
            # Clip ends at x=150.
            # Check x=100 (Global). Should be Red.
            resp = client.get_pixel(100, 60) # y=60 is inside the rect (50..100)
            if resp.get("status") == "ok":
                color = tuple(resp.get("data"))
                if color != (255, 0, 0, 255):
                    results["errors"].append(f"Pixel at (100,60) should be Red (Inside Clip), got {color}")
            
            # 2. Outside Clip Region
            # Check x=160 (Global). VG content exists here, but should be clipped.
            # Expected color: Background (Transparent/Black)
            resp = client.get_pixel(160, 60)
            if resp.get("status") == "ok":
                color = tuple(resp.get("data"))
                if color == (255, 0, 0, 255):
                    results["errors"].append(f"Pixel at (160,60) should NOT be Red (Clipped), got {color}")

    def test_vector_percentages(self):
        """Test vector graphics using percentage coordinates with padding."""
        
        def setup(window):
            # 1. VG directly in Window (200x200), with Padding 20
            # Content box: 200 - 20 - 20 = 160x160.
            # 0% = 20px. 100% = 180px.
            # Test Line: 10% -> 90%.
            # 10% of 160 = 16. + 20 = 36.
            # 90% of 160 = 144. + 20 = 164.
            # Global: (36, 36) -> (164, 164).
            
            vg = VectorGraphics(0, 0, 200, 200, padding=20, id="vg_pct")
            vg.stroke((255, 255, 0, 255), width=2) # Yellow
            vg.move_to("10%", "10%")
            vg.line_to("90%", "90%")
            
            window.add_child(vg)
            
            # 2. Add Layer/VBox test cases? 
            # The prompt requested: "directly in window, in a layer, and in a rectangle (container)".
            # We can use separate VGs for simplicity or run sub-tests. 
            # Given run_vector_test limitation (one setup), we'll add multiple VGs in different positions.
            
            # Layer Context
            # Layer at (0, 0) to avoid offset math confusion.
            layer = Layer(0, 0, 200, 200)
            # VG in Layer. Small size (100x100). Padding (10).
            # Content: 80x80.
            # 10%(8) -> 90%(72).
            # Offset 10.
            # Local: 18 -> 82.
            # Global (Layer is 0,0, VG is at 100,0? Let's place it at 100,0)
            vg_layer = VectorGraphics(100, 0, 100, 100, padding=10, id="vg_layer")
            vg_layer.stroke((0, 255, 255, 255), width=2) # Cyan
            vg_layer.move_to("0%", "0%") # Should be at padding (10,10) local -> (110, 10) global
            vg_layer.line_to("100%", "100%") # Should be at (90,90) local -> (190, 90) global
            
            layer.add_child(vg_layer)
            window.add_child(layer)
            
            # VBox Context (Rectangle)
            vbox = VBox(0, 100, 100, 100) # Bottom Left
            # VG inside. Auto size? Fixed size 100x100.
            vg_box = VectorGraphics(0,0, 100, 100, padding=0, id="vg_box") # No padding
            vg_box.stroke((255, 0, 255, 255), width=2) # Magenta
            vg_box.move_to("50%", "50%") # Center 50,50
            vg_box.line_to("100%", "50%") # Right 100,50
            # Global VBox at 0,100. VG at 0,100.
            # Center: 50, 150.
            
            vbox.add_child(vg_box)
            window.add_child(vbox)
            
        def validate(client, results):
            # 1. Window VG (Yellow)
            # Check Start (36, 36) - Approximate
            resp = client.get_pixel(36, 36)
            if resp.get("status") == "ok":
                color = tuple(resp.get("data"))
                # Just check it's not black/transparent. Yellow is (255,255,0,255)
                # Anti-aliasing might vary exact color, check R and G high
                if color[0] < 200 or color[1] < 200:
                    results["errors"].append(f"Window VG: Pixel at (36,36) should be Yellowish, got {color}")
            
            # Check End (164, 164) -> 164 might be the very edge or off by one in rasterization.
            # Check 163, 163.
            resp = client.get_pixel(163, 163)
            if resp.get("status") == "ok":
                 color = tuple(resp.get("data"))
                 if color[0] < 200 or color[1] < 200:
                    results["errors"].append(f"Window VG: Pixel at (163,163) should be Yellowish, got {color}")
            
            # Check 0% is NOT at 0,0 (Padding is 20)
            # Pixel at (10, 10) should be empty/black
            resp = client.get_pixel(10, 10)
            if resp.get("status") == "ok":
                 color = tuple(resp.get("data"))
                 if color[3] > 0 and (color[0]>50 or color[1]>50):
                      results["errors"].append(f"Window VG: Pixel at (10,10) should be Black (Padding), got {color}")

            # 2. Layer VG (Cyan)
            # Start 0% -> at padding (10,10) relative to VG (100,0) -> Global (110, 10)
            resp = client.get_pixel(110, 10)
            if resp.get("status") == "ok":
                 color = tuple(resp.get("data"))
                 # Cyan: 0, 255, 255
                 if color[1] < 200 or color[2] < 200:
                     results["errors"].append(f"Layer VG: Pixel at (110,10) should be Cyan, got {color}")
            
            # End 100% -> at (190, 90). Check (189, 89)
            resp = client.get_pixel(189, 89)
            if resp.get("status") == "ok":
                 color = tuple(resp.get("data"))
                 if color[1] < 200 or color[2] < 200:
                     results["errors"].append(f"Layer VG: Pixel at (189,89) should be Cyan, got {color}")

            # 3. VBox VG (Magenta)
            # Start 50% -> (50, 50) rel to VG (0,0,100,100) -> global (0+50, 100+50) = (50, 150)
            resp = client.get_pixel(50, 150)
            if resp.get("status") == "ok":
                 color = tuple(resp.get("data"))
                 # Magenta: 255, 0, 255
                 if color[0] < 200 or color[2] < 200:
                      results["errors"].append(f"VBox VG: Pixel at (50,150) should be Magenta, got {color}")

        self.run_vector_test(setup, validate)


if __name__ == '__main__':
    unittest.main()
