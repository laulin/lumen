import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from sdl_gui.window.window import Window
from sdl_gui import core
from sdl_gui.primitives import Input, ResponsiveText, Rectangle, Container
import sdl2.ext

def main():
    width, height = 800, 600
    
    # Create Window
    # Debug=True to show outlined boxes
    window = Window("Lumen Input Demo", width, height, debug=True)
    
    # Simple layout
    with window:
        # Background
        Rectangle(0, 0, width, height, color=(240, 240, 240))
        
        # Title
        ResponsiveText(20, 20, 760, 40, "Input Primitive Demo", size=24, align="center")
        
        # Input 1: Basic
        ResponsiveText(50, 70, 200, 30, "Name (Basic):", size=18)
        Input(50, 100, 300, 40, placeholder="Enter your name...", id="input_name")
        
        # Input 2: Max Length 10
        ResponsiveText(400, 70, 200, 30, "PC (Max 10):", size=18)
        Input(400, 100, 200, 40, placeholder="Zip Code", max_length=10, id="input_zip")
        
        # Input 3: Scrollable (Small width)
        ResponsiveText(50, 160, 200, 30, "Address (Scrolls):", size=18)
        # Small width to force scroll
        Input(50, 190, 200, 40, placeholder="Long Address...", id="input_addr")
        
        # Input 4: Multiline
        ResponsiveText(50, 250, 200, 30, "Bio (Multiline):", size=18)
        Input(50, 280, 500, 120, placeholder="Tell us about yourself...", multiline=True, id="input_bio")
        
        # Output label
        output_label = ResponsiveText(50, 450, 700, 40, "Status: Ready", color=(100, 100, 100))
        
        # We need a way to hook listeners. For demo we can iterate root children if we had refs,
        # but here we rely on ID lookups in loop or just manual binding if we kept vars.
        # Since we didn't keep vars in scope (implicit parenting), let's just find them by ID in loop if needed,
        # or better: we can't easily attach callbacks without refs.
        # Let's fix the demo to keep refs.
        
    # Re-access children to attach callbacks (Hack for demo simplicity vs structure)
    # Ideally we keep refs.
    # Let's reconstruct inputs with refs.
    
    window.root_children = [] # Reset for clarity of this block code reuse
    with window:
         ResponsiveText(20, 20, 760, 40, "Input Primitive Demo (SOTA & Versatile)", size=24, align="center")
         ResponsiveText(20, 50, 760, 20, "Try: Drag Select, Double Click, Ctrl+Z (Undo), Ctrl+Arrows, Styled Inputs", size=14, align="center", color=(80,80,80))
         
         
         ResponsiveText(500, 150, 250, 30, "Styled Input (Transparent):", size=16)
         
         # A rounded container acting as background
         # Input inside is transparent
         # Note: We need absolute coords for primitives for now in this demo structure
         bg_rect = Rectangle(500, 180, 200, 40, color=(230, 240, 255), radius=20, border_color=(100, 150, 255), border_width=2)
         inp_style = Input(510, 185, 180, 30, placeholder="Custom Style...", background_color=None, border_width=0, id="input_style")
         
         # --- Rest of Standard Inputs ---
         ResponsiveText(50, 80, 200, 30, "Name:", size=18)
         inp_name = Input(50, 110, 300, 40, placeholder="Name", id="input_name")
         
         ResponsiveText(400, 80, 200, 30, "Zip (Max 5):", size=18)
         inp_zip = Input(400, 110, 100, 40, placeholder="12345", max_length=5, id="input_zip")
         
         ResponsiveText(50, 170, 300, 30, "Long Scroll (Width 150):", size=18)
         inp_scroll = Input(50, 200, 150, 40, placeholder="Keep typing...", id="input_scroll")
         
         ResponsiveText(50, 260, 200, 30, "Bio (Multiline):", size=18)
         inp_bio = Input(50, 290, 500, 120, placeholder="Line 1\nLine 2", multiline=True, id="input_bio")
         
         status = ResponsiveText(50, 450, 700, 40, "Action: None", color=(50, 50, 50))

         def update_status(txt): status.text = f"Typing: {txt}"
         inp_name.on_change = lambda t: update_status(f"Name: {t}")
         inp_zip.on_change = lambda t: update_status(f"Zip: {t}")
         inp_scroll.on_change = lambda t: update_status(f"Scroll: {t}")
         inp_bio.on_change = lambda t: update_status(f"Bio len: {len(t)}")

    # Main Loop
    window.show()
    running = True
    while running:
        # Get UI Events
        events = window.get_ui_events()
        
        for event in events:
            if event["type"] == core.EVENT_QUIT:
                running = False
            
            # Helper for styled input feedback
            if event.get("target") == "input_style":
                if event["type"] == core.EVENT_FOCUS:
                    # Lighter and thicker border
                    bg_rect.border_color = (255, 200, 200)
                    bg_rect.border_width = 4
                elif event["type"] == core.EVENT_BLUR:
                    # Darker and thinner border
                    bg_rect.border_color = (100, 150, 255)
                    bg_rect.border_width = 2

            target_id = event.get("target")
            if target_id:
                # Dispatch mapping
                target = None
                if target_id == "input_name": target = inp_name
                elif target_id == "input_zip": target = inp_zip
                elif target_id == "input_scroll": target = inp_scroll
                elif target_id == "input_bio": target = inp_bio
                elif target_id == "input_style": target = inp_style
                
                if target:
                    target.handle_event(event, context=window)

        display_list = window.get_root_display_list()
        window.render(display_list)
        sdl2.SDL_Delay(16)

    sdl2.ext.quit()

if __name__ == "__main__":
    main()
