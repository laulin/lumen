import sys
import os
from typing import List

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import sdl2
from sdl_gui import core
from sdl_gui.core import KEY_COLOR, KEY_RECT
from sdl_gui.window.renderer import Renderer
from sdl_gui.window.window import Window
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.rectangle import Rectangle as Rect

class DemoFlexbox(Window):
    def get_initial_primitives(self) -> List:
        primitives = []
        
        # 1. Row with Space Between
        row1 = FlexBox(x=50, y=50, width=700, height=100,
                       flex_direction="row", justify_content="space_between", align_items="center",
                       id="row1")
        row1.add_child(Rect(x=0, y=0, width=50, height=50, color=(255, 0, 0, 255)))
        row1.add_child(Rect(x=0, y=0, width=50, height=80, color=(0, 255, 0, 255)))
        row1.add_child(Rect(x=0, y=0, width=50, height=50, color=(0, 0, 255, 255)))
        
        primitives.append(row1)
        
        # 2. Column with Flex Grow
        col1 = FlexBox(x=50, y=200, width=300, height=300,
                       flex_direction="column", gap=10,
                       id="col1", padding=(10, 10, 10, 10))
        # Add background to container
        col1_data = col1.to_data()
        col1_data[KEY_COLOR] = (50, 50, 50, 255) # Dark bg
        
        # Since to_data is called by window, we should construct modifying primitives directly?
        # Standard approach is: primitives list contains objects.
        # But `col1` is an object.
        # I need to set color on the object.
        # FlexBox doesn't expose color in init, but we can set it via dictionary patch or modifying class?
        # Or just use Rect as background?
        # But for this demo, let's just assume FlexBox renders color if present in data.
        # I added `if item.get(core.KEY_COLOR)` in renderer! 
        # So I can inject it.
        # However, `FlexBox` class stores props in self.
        # `to_data` builds the dict.
        # I can subclass or just monkeypatch or rely on the fact that `Window` calls `to_data`.
        
        # Proper way:
        # Create a RectContainer or similar?
        pass

        # Let's rebuild col1 with a wrapper or just use `to_data` override.
        # Simpler: The `FlexBox` primitive should ideally support color.
        # But for now, let's just add children.
        
        c1 = Rect(x=0, y=0, width="100%", height=50, color=(200, 200, 0, 255))
        c2 = Rect(x=0, y=0, width="100%", height=50, color=(0, 200, 200, 255))
        c3 = Rect(x=0, y=0, width="100%", height=0, color=(200, 0, 200, 255)) 
        # c3 should grow. But Rect doesn't have flex props in init.
        # Primitives are just data generators.
        # I need to inject flex props into the generated data.
        # The `FlexBox` primitive calls `to_data` on children.
        # I should probably update `BasePrimitive` to support kwargs for flex props?
        # Or just manipulate the dict returned by child.
        
        # The cleanest way without modifying BasePrimitive:
        # Manually create dict or helper.
        
        return primitives

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_children = self.get_initial_primitives()

    def run(self):
        self.show()
        running = True
        while running:
             events = self.get_ui_events()
             for event in events:
                 if event.get("type") == core.EVENT_QUIT:
                     running = False
             
             # Re-resolve primitives if needed (e.g. for dynamic changes)
             # But here we just use what we have.
             # Wait, get_root_display_list calls to_data().
             display_list = self.get_root_display_list()
             
             # Hack for demo color injection as previously discussed
             self._inject_demo_styles(display_list)
             
             self.render(display_list)
             import time
             time.sleep(0.016) # ~60 FPS

    def _inject_demo_styles(self, display_list):
        for item in display_list:
            if item.get("id") == "col1":
                # Inject background color
                item[KEY_COLOR] = (50, 50, 50, 255)
            
            # Recursively check children
            if "children" in item:
                self._inject_demo_styles(item["children"])

if __name__ == "__main__":
    win = DemoFlexbox(width=800, height=600, title="Flexbox Demo")
    win.run()
