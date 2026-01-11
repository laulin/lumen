import sys
import os
import random
import time
import sdl2
import sdl2.ext

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from sdl_gui.window.window import Window
from sdl_gui import core
from sdl_gui.primitives.vector_graphics import VectorGraphics

def main():
    # Initialize Window
    window = Window(title="Simple Dynamic Chart", width=800, height=600, debug=True)
    
    # Create VectorGraphics filling the window
    chart = VectorGraphics("0%", "0%", "100%", "100%", padding=(20, 20, 20, 20), id="dynamic_chart")
    window.add_child(chart)
    
    # Show window
    window.show()
    
    running = True
    points = [50 + random.random() * 50]
    max_points = 50
    last_update = time.time()
    
    while running:
        # Event Loop
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    running = False
        
        # Update Data randomly
        now = time.time()
        if now - last_update > 0.05: # Update every 50ms
            last_update = now
            
            # Random walk
            last_val = points[-1]
            change = random.uniform(-5, 5)
            new_val = last_val + change
            # Clamp
            new_val = max(10, min(90, new_val))
            points.append(new_val)
            if len(points) > max_points:
                points.pop(0)
            
            # Re-draw chart
            chart.clear()
            
            # Draw Grid
            chart.stroke((50, 50, 50, 255), width=1)
            chart.move_to("0%", "50%")
            chart.line_to("100%", "50%")
            
            # Draw Dynamic Line
            if points:
                chart.stroke((0, 255, 0, 255), width=3)
                
                # Calculate points
                path_points = []
                for i, val in enumerate(points):
                    x_pct = (i / (max_points - 1)) * 100
                    y_pct = 100 - val # Invert Y for screen coords
                    path_points.append((f"{x_pct}%", f"{y_pct}%"))
                
                chart.move_to(path_points[0][0], path_points[0][1])
                for x, y in path_points[1:]:
                    chart.line_to(x, y)

        display_list = window.get_root_display_list()
        window.render(display_list)
        sdl2.SDL_Delay(16)

if __name__ == "__main__":
    main()
