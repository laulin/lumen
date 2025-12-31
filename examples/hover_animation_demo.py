import sys
import os
import time
import ctypes
import sdl2
import sdl2.ext

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdl_gui.window.window import Window
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui import core

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    """Linear interpolation between two colors."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
        int(c1[3] + (c2[3] - c1[3]) * t)
    )

class AnimatedItem:
    def __init__(self, rect, animation_type, **kwargs):
        self.rect = rect
        self.animation_type = animation_type
        self.hover_t = 0.0
        self.base_x = rect.x
        self.base_y = rect.y
        self.base_w = rect.width
        self.base_h = rect.height
        self.base_color = rect.color
        self.target_color = kwargs.get('target_color', rect.color)
        self.kwargs = kwargs

    def update(self, dt, mx, my):
        # Hit Test
        # Note: For scaling items, we should ideally test against the *visual* rect or the *base* rect?
        # Usually base rect avoids jitter at edges, but visual rect feels more natural.
        # Let's use current visual rect logic (handled by hit_test rect usage) 
        # BUT for stability, let's test against the BASE rect for the trigger area to avoid 
        # "mouse barely in -> expands -> mouse definitely in" loops or reverse "mouse out -> shrinks -> mouse in" loops.
        # Stability is key. Base rect is safer.
        is_hovered = (self.base_x <= mx < self.base_x + self.base_w) and \
                     (self.base_y <= my < self.base_y + self.base_h)

        # Update t
        direction = 1.0 if is_hovered else -1.0
        self.hover_t += direction * (dt / 1.0) # 1.0 second duration
        self.hover_t = max(0.0, min(1.0, self.hover_t))

        t = self.hover_t

        # Apply specific animation logic
        if self.animation_type == 'fade_fill':
            # Fade alpha of fill from 0 to target (or specific alpha)
            # Base is transparent-ish or just 0 alpha? 
            # Request: "transparent to given color"
            # So start color should have 0 alpha.
            # self.base_color is set in init.
            current = lerp_color(self.base_color, self.target_color, t)
            self.rect.color = current

        elif self.animation_type == 'scale':
            # EXPAND 120%
            scale = lerp(1.0, 1.2, t)
            new_w = int(self.base_w * scale)
            new_h = int(self.base_h * scale)
            
            # Center adjustment
            # diff_w = new_w - self.base_w => shift x by -diff_w / 2
            diff_w = new_w - self.base_w
            diff_h = new_h - self.base_h
            
            self.rect.width = new_w
            self.rect.height = new_h
            self.rect.x = int(self.base_x - diff_w / 2)
            self.rect.y = int(self.base_y - diff_h / 2)

        elif self.animation_type == 'move':
            # Move UP 10px
            # Up means Y decreases
            offset = lerp(0, -10, t)
            self.rect.y = int(self.base_y + offset)


def main():
    width, height = 800, 400
    with Window("Advanced Hover Animations", width, height, debug=True) as win:
        
        items = []
        
        # 1. Fade Fill (Rounded, Fixed Border)
        # Start transparent fill
        r1 = Rectangle(100, 150, 100, 100, 
                       color=(0, 255, 0, 0), # Transparent Green start
                       radius=15,
                       border_color=(0, 255, 0, 255), # Solid Green Border
                       border_width=2)
        items.append(AnimatedItem(r1, 'fade_fill', target_color=(0, 255, 0, 255)))
        
        # 2. Scale (expands)
        r2 = Rectangle(350, 150, 100, 100, 
                       color=(100, 100, 255, 255), # Blue
                       radius=0)
        items.append(AnimatedItem(r2, 'scale'))

        # 3. Move (shifts up)
        r3 = Rectangle(600, 150, 100, 100, 
                       color=(255, 100, 255, 255), # Pink
                       radius=0)
        items.append(AnimatedItem(r3, 'move'))
        
        # Labels
        labels = [
            ResponsiveText(100, 270, 100, "auto", text="Fade Fill", align="center", size=14),
            ResponsiveText(350, 270, 100, "auto", text="Scale", align="center", size=14),
            ResponsiveText(600, 270, 100, "auto", text="Move", align="center", size=14),
        ]

        running = True
        last_time = time.time()
        print("Starting main loop...")
        
        while running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Events
            events = sdl2.ext.get_events()
            for event in events:
                if event.type == sdl2.SDL_QUIT:
                    running = False
            
            # Mouse
            x, y = ctypes.c_int(0), ctypes.c_int(0)
            sdl2.mouse.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
            mx, my = x.value, y.value
            
            # Update Items
            display_list = []
            
            # Bg
            display_list.append(Rectangle(0, 0, width, height, color=(30, 30, 30, 255)).to_data())
            
            for item in items:
                item.update(dt, mx, my)
                display_list.append(item.rect.to_data())
                
            for label in labels:
                display_list.append(label.to_data())
            
            win.render(display_list)
            #sdl2.SDL_Delay(16)

    sdl2.ext.quit()

if __name__ == "__main__":
    main()
