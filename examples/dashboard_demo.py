import sys
import os
import math
import random
import time
from datetime import datetime

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import sdl2
import sdl2.ext
from sdl_gui import core
from sdl_gui.window.window import Window
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.vector_graphics import VectorGraphics

# --- Theme Constants (Kibana Dark Style) ---
C_BG_DARK = (20, 23, 28, 255)       # Main Background
C_PANEL_BG = (27, 31, 36, 255)      # Widget/Panel Background
C_PANEL_BORDER = (45, 50, 58, 255)  # Widget Border
C_ACCENT = (0, 120, 255, 255)       # Primary Blue
C_TEXT_MAIN = (223, 229, 239, 255)  # Main Text
C_TEXT_SEC = (152, 162, 179, 255)   # Secondary Text (Grey)

C_CHART_1 = (0, 184, 144, 255)      # Green/Teal
C_CHART_2 = (245, 102, 102, 255)    # Red/Salmon
C_CHART_3 = (245, 180, 50, 255)     # Yellow/Orange
C_CHART_4 = (100, 100, 255, 255)    # Blue

class DashboardDemo(Window):
    def __init__(self):
        super().__init__("Ops Dashboard - Vector Graphics Demo", 1280, 800, debug=True)
        self.root_children = self.get_ui_layout()
        self.last_update = time.time()
        self.points_cache = [random.randint(20, 80) for _ in range(30)] # Simulated Live Data

    def get_ui_layout(self):
        root = FlexBox(x=0, y=0, width="100%", height="100%", 
                      flex_direction="column", id="root")
        
        # Background
        bg = Rectangle(x=0, y=0, width="100%", height="100%", color=C_BG_DARK)
        
        # Top Bar
        top_bar = self._create_top_bar()
        root.add_child(top_bar)
        
        # Main Content Grid
        content = FlexBox(x=0, y=0, width="100%", height="auto",
                         flex_direction="row", 
                         padding=(20, 20, 20, 20), gap=20).set_flex_grow(1)
        
        # Left Col (Stats)
        left_col = FlexBox(x=0, y=0, width="250px", height="100%", flex_direction="column", gap=20)
        left_col.set_flex_shrink(0)
        left_col.add_child(self._create_stat_card("CPU Usage", "42%", C_CHART_1))
        left_col.add_child(self._create_stat_card("Memory", "12.8 GB", C_CHART_2))
        left_col.add_child(self._create_stat_card("Network", "1.2 MB/s", C_CHART_3))
        left_col.add_child(self._create_gauge_widget())
        
        # Right Col (Charts)
        right_col = FlexBox(x=0, y=0, width="auto", height="100%", flex_direction="column", gap=20).set_flex_grow(1)
        
        # Row 1: Line Chart (Live)
        self.line_chart = self._create_line_chart_widget()
        right_col.add_child(self.line_chart)
        
        # Row 2: Two Smaller Charts
        bottom_row = FlexBox(x=0, y=0, width="100%", height="50%", flex_direction="row", gap=20)
        bottom_row.add_child(self._create_bar_chart_widget())
        bottom_row.add_child(self._create_pie_chart_widget())
        
        right_col.add_child(bottom_row)
        
        content.add_child(left_col)
        content.add_child(right_col)
        
        root.add_child(content)
        
        return [bg, root]

    def _create_top_bar(self):
        header = FlexBox(x=0, y=0, width="100%", height="60px", 
                        flex_direction="row", align_items="center", 
                        padding=(0, 20, 0, 20), gap=20)
        header.set_color(C_PANEL_BG)
        # Underscore border
        # Using a primitive line logic or border-bottom logic if FlexBox supported specific borders.
        # FlexBox supports uniform border. We use a rectangle at bottom?
        # For now just flat panel.
        
        title = ResponsiveText(x=0, y=0, width="auto", height="auto", text="SYSTEM OPERATIONS", size=20, color=C_TEXT_MAIN)
        date_lbl = ResponsiveText(x=0, y=0, width="auto", height="auto", text=datetime.now().strftime("%Y-%m-%d"), size=14, color=C_TEXT_SEC)
        
        spacer = FlexBox(x=0, y=0, width="auto", height="auto").set_flex_grow(1)
        
        user_lbl = ResponsiveText(x=0, y=0, width="auto", height="auto", text="admin@lumen.dev", size=14, color=C_ACCENT)
        
        header.add_child(title)
        header.add_child(spacer)
        header.add_child(date_lbl)
        header.add_child(user_lbl)
        return header

    def _create_panel(self, w="100%", h="auto", grow=0):
        p = FlexBox(x=0, y=0, width=w, height=h, padding=(15, 15, 15, 15), flex_direction="column")
        if grow: p.set_flex_grow(grow)
        p.set_color(C_PANEL_BG)
        p.set_radius(6)
        p.set_border_width(1)
        p.set_border_color(C_PANEL_BORDER)
        return p

    def _create_stat_card(self, title, value, color):
        card = self._create_panel(h="100px")
        
        lbl = ResponsiveText(x=0, y=0, width="auto", height="auto", text=title, size=14, color=C_TEXT_SEC)
        val = ResponsiveText(x=0, y=0, width="auto", height="auto", text=value, size=32, color=C_TEXT_MAIN)
        
        # Small Indicator Dot
        dot = VectorGraphics(x=0, y=0, width=10, height=10)
        dot.fill(color).circle(5, 5, 4)
        
        row = FlexBox(x=0, y=0, width="100%", height="auto", flex_direction="row", align_items="center", gap=10)
        row.add_child(dot)
        row.add_child(lbl)
        
        card.add_child(row)
        card.add_child(val)
        return card

    def _create_line_chart_widget(self):
        panel = self._create_panel(h="50%", grow=1)
        
        header = FlexBox(x=0, y=0, width="100%", height="auto", flex_direction="row", justify_content="space_between")
        header.add_child(ResponsiveText(x=0, y=0, width="auto", height="auto", text="Traffic Analysis (Live)", size=16, color=C_TEXT_MAIN))
        
        # The Line Chart Area
        # Because layout is dynamic, we give the vector graphics "100%" size.
        # But the vector primitive needs to know its size to normalize drawing if we use relative 0..1 coords,
        # OR we just draw assuming a fixed coordinate system and scale?
        # Better: we redraw the vector commands every frame based on ACTUAL size.
        # But `VectorGraphics` primitives are static instructions.
        # So we need to update instructions in the update loop.
        
        self.vg_line = VectorGraphics(x=0, y=0, width="100%", height="100%", id="line_chart")
        # We'll set commands in update()
        
        chart_container = FlexBox(x=0, y=0, width="100%", height="100%", padding=(10,0,0,0))
        chart_container.set_flex_grow(1)
        chart_container.add_child(self.vg_line)
        
        panel.add_child(header)
        panel.add_child(chart_container)
        return panel

    def _create_bar_chart_widget(self):
        panel = self._create_panel(w="50%", h="100%")
        panel.add_child(ResponsiveText(x=0, y=0, width="auto", height="auto", text="Request Distribution", size=16, color=C_TEXT_MAIN))
        
        vg = VectorGraphics(x=0, y=0, width="100%", height="100%", id="bar_chart")
        
        # Static Bar Chart for Demo
        # We assume some size, say 400x300, but it will scale if we draw intelligently?
        # Since we can't easily read resolved size here in init, we might layout based on percentages?
        # No, vector commands are pixel integers. 
        # So for a RESIZABLE chart, we need to regenerate commands on resize or update.
        # For this demo, let's assume update loop handles it.
        
        self.vg_bar = vg
        
        container = FlexBox(x=0, y=0, width="100%", height="100%", padding=(10,0,0,0))
        container.set_flex_grow(1)
        container.add_child(vg)
        panel.add_child(container)
        return panel

    def _create_pie_chart_widget(self):
        panel = self._create_panel(w="50%", h="100%")
        panel.add_child(ResponsiveText(x=0, y=0, width="auto", height="auto", text="Error Rate", size=16, color=C_TEXT_MAIN))
        
        vg = VectorGraphics(x=0, y=0, width="100%", height="100%")
        self.vg_pie = vg
        
        container = FlexBox(x=0, y=0, width="100%", height="100%")
        container.set_flex_grow(1)
        container.add_child(vg)
        panel.add_child(container)
        return panel

    def _create_gauge_widget(self):
        panel = self._create_panel(h="200px")
        panel.add_child(ResponsiveText(x=0, y=0, width="auto", height="auto", text="Server Load", size=14, color=C_TEXT_SEC))
        
        vg = VectorGraphics(x=0, y=0, width="100%", height="100%")
        self.vg_gauge = vg
        
        container = FlexBox(x=0, y=0, width="100%", height="100%")
        container.set_flex_grow(1)
        container.add_child(vg)
        panel.add_child(container)
        return panel

    def _update_charts(self):
        # We need the resolved size of the widgets to draw correctly.
        # In a real app, the layout engine resolves sizes, and we can access them.
        # But we don't have direct access to the resolved rects of primitives easily unless we query renderer or check object properties if updated.
        # The renderer calls 'to_data' which reads properties.
        # The renderer renders based on layout.
        # For this demo, we can *guess* sizes or use fixed logic if window is fixed. 
        # But user wants "Kibana styling" which implies responsiveness.
        # Hack: The renderer updates the `_measurement_cache`? No.
        # The primitives don't automatically get their resolved rects back from renderer currently.
        
        # Workaround: Assume a reasonable coordinate space (e.g. 0-1000) and scale?
        # Or just hardcode logic based on known window size for the Demo.
        # But `VectorGraphics` creates a texture of `width` x `height`.
        # If we set width="100%", the renderer calculates `w`.
        # Then `_render_vector_graphics` creates texture of size `w`.
        # Our commands need to fit in `w`.
        # How do we know `w` when generating commands?
        # We don't. This is a Catch-22 of the current architecture.
        # Solution: 
        # 1. Update architecture to pass size to primitives?
        # 2. Or, for the demo, use `Window.renderer.get_last_display_list()` to find the resolved rects?
        # That's possible!
        
        hit_list = self.renderer.get_hit_list() 
        # But hit_list is rebuilt every frame.
        pass

    def run(self):
        self.show()
        running = True
        while running:
            # Event Loop
            events = self.get_ui_events()
            for event in events:
                if event.get("type") == core.EVENT_QUIT: running = False
                elif event.get("type") == core.EVENT_KEY_DOWN:
                     if event.get("key_sym") == sdl2.SDLK_ESCAPE: running = False

            # Update Logic (Simulate Animation)
            now = time.time()
            if now - self.last_update > 0.1: # 10 FPS data update
                self.last_update = now
                self.points_cache.pop(0)
                self.points_cache.append(random.randint(20, 80))
            
            # Re-generate commands based on approximate layout
            # (In a real app, we'd have a layout callback)
            self._draw_line_chart()
            self._draw_bar_chart()
            self._draw_pie_chart()
            self._draw_gauge()

            display_list = self.get_root_display_list()
            self.render(display_list)
            # sdl2.SDL_Delay(16) # Cap to ~60fps
            
        sdl2.ext.quit()

    def _draw_line_chart(self):
        # We approximate the size: width ~ 900, height ~ 300
        w, h = 900, 300
        vg = self.vg_line.clear()
        
        # Grid
        vg.stroke((60, 60, 65), 1)
        for i in range(5):
             y = int(h * (i/4))
             vg.move_to(0, y).line_to(w, y)
             
        # Path
        vg.stroke(C_ACCENT, 2)
        step_x = w / (len(self.points_cache) - 1)
        
        # Build path points
        pts = []
        for i, val in enumerate(self.points_cache):
             px = int(i * step_x)
             py = int(h - (val / 100 * h))
             pts.append((px, py))
             
        if pts:
            vg.move_to(pts[0][0], pts[0][1])
            for i in range(1, len(pts)):
                # Smooth curve? Or straight lines. 
                # Straight lines are faster/easier for now.
                vg.line_to(pts[i][0], pts[i][1])
                
            # Fill area (Gradient simulation via multiple lines? Too heavy)
            # Just fill under?
            # To fill under, we need a closed shape.
            # vg.fill((0, 120, 255, 50)) # Transparent blue
            # But currently fill() fills the SHAPE defined by cmds.
            # If we just did lines, we have an open path.
            # We need to close it:
            vg.line_to(w, h).line_to(0, h).line_to(pts[0][0], pts[0][1])
            vg.fill((0, 120, 255, 30))

        vg.set_cache_key(f"line_{int(time.time() * 10)}") # dynamic cache key for animation

    def _draw_bar_chart(self):
        w, h = 400, 250
        vg = self.vg_bar.clear()
        
        data = [30, 50, 80, 40, 90, 20]
        bar_w = (w / len(data)) - 10
        
        for i, val in enumerate(data):
            bx = int(i * (bar_w + 10) + 5)
            bh = int((val / 100) * h)
            by = h - bh
            
            # Bar
            color = C_CHART_1 if i % 2 == 0 else C_CHART_2
            vg.fill(color).rect(bx, by, int(bar_w), bh)

        vg.set_cache_key("bar_static")

    def _draw_pie_chart(self):
        w, h = 400, 250
        cx, cy = w//2, h//2
        r = min(w, h) // 2 - 20
        vg = self.vg_pie.clear()
        
        slices = [30, 70, 45, 100] # degrees
        colors = [C_CHART_1, C_CHART_2, C_CHART_3, C_CHART_4]
        
        start = 0
        for i, sweep in enumerate(slices):
            end = start + sweep
            vg.fill(colors[i]).pie(cx, cy, r, start, end)
            start = end
            
        # Inner Circle for Donut
        vg.fill(C_PANEL_BG).circle(cx, cy, r // 2)
        
        vg.set_cache_key("pie_static")

    def _draw_gauge(self):
         w, h = 200, 150
         cx, cy = w//2, h - 20
         r = 100
         vg = self.vg_gauge.clear()
         
         # Background Arc
         vg.stroke(C_PANEL_BORDER, 10).arc(cx, cy, r, 180, 360)
         
         # Value Arc
         val = self.points_cache[-1] # 0-100
         angle = 180 + (val / 100 * 180)
         
         start = 180
         # We can't do single thick arc easily with current primitive unless we use `pie` or thick line path
         # sdlgfx arc width is 1px usually unless we use thickLine?
         # But curve is hard with lines.
         # Actually `pie` works for filled sector.
         # Let's use pie for gauge sector?
         
         vg.fill(C_ACCENT).pie(cx, cy, r, 180, int(angle))
         # Cutout center
         vg.fill(C_PANEL_BG).pie(cx, cy, r-10, 180, 360) # Overdraw to mask inner
         
         vg.set_cache_key(f"gauge_{val}")


if __name__ == "__main__":
    demo = DashboardDemo()
    demo.run()
