import sys
import os
import time
from typing import List, Tuple

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import sdl2.ext
from sdl_gui import core
from sdl_gui.window.window import Window
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.image import Image

# Styling Constants
COLOR_BG = (18, 18, 20, 255)
COLOR_CARD_BG = (30, 30, 35, 255)
COLOR_ACCENT = (100, 180, 255, 255)
COLOR_TEXT_MAIN = (240, 240, 240, 255)
COLOR_TEXT_SEC = (180, 180, 180, 255)
COLOR_SUCCESS = (80, 200, 120, 255)
COLOR_WARNING = (255, 180, 50, 255)

class BeautifulFlexDemo(Window):
    def __init__(self):
        super().__init__("Lumen Flexbox Showcase", 1000, 800, debug=True)
        self.root_children = self.get_ui_layout()

    def get_ui_layout(self) -> List:
        # Root Container (Column) using FlexBox
        root = FlexBox(x=0, y=0, width="100%", height="100%",
                      flex_direction="column", 
                      padding=(20, 20, 20, 20),
                      gap=20,
                      id="root")
        
        # 1. Header Section
        header = self._create_header()
        root.add_child(header)
        
        # 2. Key Features Grid (Responsive Row)
        features = self._create_features_section()
        root.add_child(features)
        
        # 3. Complex Nested UI (Card with Badge)
        card_section = self._create_complex_card_section()
        root.add_child(card_section)
        
        # 4. Alignment Playground
        playground = self._create_alignment_playground()
        root.add_child(playground)

        # Apply Global Background
        bg = Rectangle(x=0, y=0, width="100%", height="100%", color=COLOR_BG)
        # We return [bg, root] to layer basic background then content
        # Note: renderer draws in order.
        return [bg, root]

    def _create_header(self):
        header_box = FlexBox(x=0, y=0, width="100%", height="auto",
                            flex_direction="column",
                            align_items="center",
                            gap=10)
        
        title = ResponsiveText(x=0, y=0, width="100%", height="auto",
                              text="Lumen Flexbox Engine",
                              size=32, color=COLOR_ACCENT, align="center")
        
        subtitle = ResponsiveText(x=0, y=0, width="100%", height="auto",
                                 text="State-of-the-art Layout System for Python SDL2",
                                 size=18, color=COLOR_TEXT_SEC, align="center")
        
        header_box.add_child(title)
        header_box.add_child(subtitle)
        return header_box

    def _create_features_section(self):
        # A row of 3 feature cards
        row = FlexBox(x=0, y=0, width="100%", height="auto",
                     flex_direction="row",
                     justify_content="space_between",
                     gap=20)
        
        f1 = self._create_feature_box("Responsive", "Adapts to screen size", COLOR_SUCCESS)
        f1.set_flex_grow(1)
        f1.set_flex_basis(0) # Equal width
        
        f2 = self._create_feature_box("Easy API", "Simple intuitive props", COLOR_WARNING)
        f2.set_flex_grow(1).set_flex_basis(0)
        
        f3 = self._create_feature_box("Fast", "Optimized Python Layout", COLOR_ACCENT)
        f3.set_flex_grow(1).set_flex_basis(0)
        
        row.add_child(f1)
        row.add_child(f2)
        row.add_child(f3)
        return row

    def _create_feature_box(self, title, desc, accent):
        box = FlexBox(x=0, y=0, width="auto", height=120,
                     flex_direction="column",
                     justify_content="center",
                     align_items="center",
                     padding=(15, 15, 15, 15),
                     gap=5)
        # Using Rectangle as background primitive injected via extra props or separate child?
        # Creating a background child that fills this box is tricky if box size is dynamic.
        # But FlexBox primitives in renderer render BACKGROUND if color is set.
        # So we can set generic props.
        box.set_color(COLOR_CARD_BG)
        box.set_radius(12)
        box.set_border_width(1)
        box.set_border_color(accent) # Colored border
        
        t = ResponsiveText(x=0, y=0, width="100%", height="auto",
                          text=title, size=20, color=COLOR_TEXT_MAIN, align="center")
        d = ResponsiveText(x=0, y=0, width="100%", height="auto",
                          text=desc, size=14, color=COLOR_TEXT_SEC, align="center")
        
        box.add_child(t)
        box.add_child(d)
        return box

    def _create_complex_card_section(self):
        # Demonstrate nested row/col and image
        container = FlexBox(x=0, y=0, width="100%", height=200,
                           flex_direction="row",
                           align_items="center",
                           gap=30)
        container.set_color((25, 25, 28, 255))
        container.set_radius(16)
        container.set_padding(20)
        
        # Left: Image Placeholder
        # Since we might not have assets, use a colored rect acting as image
        img_placeholder = Rectangle(x=0, y=0, width=160, height=160, color=(50, 50, 60, 255))
        img_placeholder.set_radius(12)
        # Fixed size
        
        # Right: Content
        content = FlexBox(x=0, y=0, width="auto", height="auto",
                         flex_direction="column",
                         justify_content="center",
                         gap=10)
        content.set_flex_grow(1) # Take remaining space
        
        # Header Row (Title + Badge)
        header_row = FlexBox(x=0, y=0, width="100%", height="auto",
                            flex_direction="row",
                            align_items="center",
                            gap=10)
        
        name = ResponsiveText(x=0, y=0, width="auto", height="auto",
                             text="Nebula Dashboard", size=24, color=COLOR_TEXT_MAIN)
        
        badge = FlexBox(x=0, y=0, width="auto", height="auto", padding=(5, 10, 5, 10))
        badge.set_color(COLOR_ACCENT)
        badge.set_radius(12)
        badge_text = ResponsiveText(x=0, y=0, width="auto", height="auto",
                                   text="PRO", size=12, color=(0,0,0,255))
        badge.add_child(badge_text)
        
        header_row.add_child(name)
        header_row.add_child(badge)
        
        desc = ResponsiveText(x=0, y=0, width="100%", height="auto",
                             text="Manage your cloud resources with intuitive controls using our new Flex layout engine. It supports complex nesting and alignment.",
                             size=14, color=COLOR_TEXT_SEC, wrap=True)
        
        # Button Row
        btn_row = FlexBox(x=0, y=0, width="100%", height="auto", flex_direction="row", gap=10)
        btn1 = self._create_button("Launch", filled=True)
        btn2 = self._create_button("Documentation", filled=False)
        btn_row.add_child(btn1)
        btn_row.add_child(btn2)
        
        content.add_child(header_row)
        content.add_child(desc)
        content.add_child(btn_row)
        
        container.add_child(img_placeholder)
        container.add_child(content)
        
        return container

    def _create_button(self, label, filled=True):
        btn = FlexBox(x=0, y=0, width="auto", height="auto", padding=(8, 20, 8, 20))
        btn.set_radius(6)
        
        if filled:
            btn.set_color(COLOR_ACCENT)
            text_color = (0,0,0,255)
        else:
            btn.set_border_width(1)
            btn.set_border_color(COLOR_ACCENT)
            text_color = COLOR_ACCENT
            
        t = ResponsiveText(x=0, y=0, width="auto", height="auto",
                          text=label, size=14, color=text_color)
        btn.add_child(t)
        return btn

    def _create_alignment_playground(self):
        # Section Header
        sec = FlexBox(x=0, y=0, width="100%", height="auto", flex_direction="column", gap=10)
        
        label = ResponsiveText(x=0, y=0, width="100%", height="auto",
                              text="Alignment Playground (Justify Content)",
                              size=18, color=COLOR_TEXT_MAIN)
        sec.add_child(label)
        
        # Row of small visualizers
        row = FlexBox(x=0, y=0, width="100%", height=120, flex_direction="row", gap=20)
        
        configs = [
            ("flex_start", "Start"),
            ("center", "Center"),
            ("space_between", "Space Between"),
            ("space_evenly", "Space Evenly")
        ]
        
        for mode, name in configs:
            viz = FlexBox(x=0, y=0, width="auto", height="100%",
                         flex_direction="row",
                         justify_content=mode,
                         align_items="center",
                         padding=(5,5,5,5))
            viz.set_flex_grow(1)
            viz.set_color((40, 40, 45, 255))
            viz.set_radius(8)
            
            # Add 3 dots
            for _ in range(3):
                dot = Rectangle(x=0, y=0, width=15, height=15, color=COLOR_WARNING)
                dot.set_radius(7)
                viz.add_child(dot)
                
            # Label overlay? Or just text below.
            # Using absolute positioning hacks or just a container.
            # Let's wrap viz in a col to add label.
            wrapper = FlexBox(x=0, y=0, width="auto", height="100%", flex_direction="column", gap=5)
            wrapper.set_flex_grow(1)
            
            lbl = ResponsiveText(x=0, y=0, width="100%", height=20, text=name, size=12, color=COLOR_TEXT_SEC, align="center")
            
            wrapper.add_child(viz)
            wrapper.add_child(lbl)
            
            row.add_child(wrapper)
            
        sec.add_child(row)
        return sec

    def run(self):
        self.show()
        running = True
        while running:
             events = self.get_ui_events()
             for event in events:
                 if event.get("type") == core.EVENT_QUIT:
                     running = False
                 if event.get("type") == core.EVENT_KEY_DOWN:
                      if event.get("key_sym") == sdl2.SDLK_ESCAPE:
                          running = False
             
             display_list = self.get_root_display_list()
             self.render(display_list)
             time.sleep(0.016)
        
        sdl2.ext.quit()

if __name__ == "__main__":
    demo = BeautifulFlexDemo()
    demo.run()
