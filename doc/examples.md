# Examples

This document provides complete, runnable code examples for common use cases.

## Basic Window

A minimal Lumen application:

```python
import sdl2.ext
from sdl_gui.window.window import Window
from sdl_gui.layers.layer import Layer
from sdl_gui.primitives.rectangle import Rectangle

def main():
    # Create window
    win = Window("Basic Example", 800, 600)
    
    # Create a layer with a colored rectangle
    layer = Layer(0, 0, "100%", "100%")
    layer.add_child(Rectangle("10%", "10%", "80%", "80%", (100, 150, 255, 255)))
    
    # Main loop
    running = True
    while running:
        for event in win.get_ui_events():
            if event.get("type") == "quit":
                running = False
        
        win.render([layer.to_data()])
    
    win.close()

if __name__ == "__main__":
    main()
```

---

## Responsive Layout

A responsive layout with header, sidebar, and content:

```python
from sdl_gui.window.window import Window
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.primitives.responsive_text import ResponsiveText

def main():
    win = Window("Responsive Layout", 1024, 768)
    
    # Root container
    root = FlexBox(0, 0, "100%", "100%", flex_direction="column")
    
    # Header
    header = FlexBox(0, 0, "100%", 60, 
                     flex_direction="row", 
                     align_items="center",
                     padding=(0, 20, 0, 20))
    header.set_color((40, 40, 45, 255))
    
    logo = ResponsiveText(0, 0, "auto", "auto", text="MyApp", 
                         size=24, color=(100, 180, 255, 255))
    header.add_child(logo)
    root.add_child(header)
    
    # Body: Sidebar + Content
    body = FlexBox(0, 0, "100%", "auto", flex_direction="row")
    body.set_flex_grow(1)
    
    # Sidebar
    sidebar = FlexBox(0, 0, 250, "100%", 
                      flex_direction="column", 
                      padding=(20, 20, 20, 20),
                      gap=10)
    sidebar.set_color((30, 30, 35, 255))
    
    for item in ["Dashboard", "Settings", "Profile", "Logout"]:
        menu_item = ResponsiveText(0, 0, "100%", 40, text=item,
                                   size=16, color=(200, 200, 200, 255))
        sidebar.add_child(menu_item)
    
    body.add_child(sidebar)
    
    # Main content
    content = FlexBox(0, 0, "auto", "100%", 
                      flex_direction="column",
                      padding=(30, 30, 30, 30))
    content.set_flex_grow(1)
    content.set_color((25, 25, 28, 255))
    
    title = ResponsiveText(0, 0, "100%", "auto", text="Welcome!",
                          size=32, color=(255, 255, 255, 255))
    content.add_child(title)
    
    body.add_child(content)
    root.add_child(body)
    
    # Render loop
    running = True
    while running:
        for event in win.get_ui_events():
            if event.get("type") == "quit":
                running = False
        win.render([root.to_data()])
    
    win.close()

if __name__ == "__main__":
    main()
```

---

## Interactive Button

A clickable button with hover effects:

```python
from sdl_gui.window.window import Window
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.responsive_text import ResponsiveText

class Button:
    def __init__(self, label, on_click):
        self.label = label
        self.on_click = on_click
        self.hovered = False
        self.id = f"btn_{label.lower().replace(' ', '_')}"
    
    def render(self):
        color = (120, 180, 255, 255) if self.hovered else (100, 150, 255, 255)
        
        btn = FlexBox(0, 0, "auto", 45,
                      justify_content="center",
                      align_items="center",
                      padding=(0, 30, 0, 30),
                      id=self.id,
                      listen_events=["click", "hover_start", "hover_end"])
        btn.set_color(color)
        btn.set_radius(8)
        
        text = ResponsiveText(0, 0, "auto", "auto", 
                             text=self.label,
                             size=16, 
                             color=(255, 255, 255, 255))
        btn.add_child(text)
        return btn
    
    def handle_event(self, event):
        event_type = event.get("type")
        if event_type == "click":
            self.on_click()
        elif event_type == "hover_start":
            self.hovered = True
        elif event_type == "hover_end":
            self.hovered = False

def main():
    win = Window("Button Example", 400, 300)
    
    counter = [0]
    def increment():
        counter[0] += 1
        print(f"Clicked! Count: {counter[0]}")
    
    button = Button("Click Me", increment)
    
    running = True
    while running:
        for event in win.get_ui_events():
            if event.get("type") == "quit":
                running = False
            elif event.get("target") == button.id:
                button.handle_event(event)
        
        # Build UI
        root = FlexBox(0, 0, "100%", "100%",
                       justify_content="center",
                       align_items="center")
        root.set_color((30, 30, 35, 255))
        root.add_child(button.render())
        
        win.render([root.to_data()])
    
    win.close()

if __name__ == "__main__":
    main()
```

---

## Form with Input Fields

A login form with text inputs:

```python
from sdl_gui.window.window import Window
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.input import Input

def main():
    win = Window("Login Form", 500, 400)
    
    # Create inputs
    username = Input(0, 0, "100%", 45,
                    placeholder="Username",
                    id="username",
                    radius=8,
                    background_color=(40, 40, 45, 255),
                    color=(255, 255, 255, 255),
                    border_color=(100, 100, 100, 255))
    
    password = Input(0, 0, "100%", 45,
                    placeholder="Password",
                    id="password",
                    radius=8,
                    background_color=(40, 40, 45, 255),
                    color=(255, 255, 255, 255),
                    border_color=(100, 100, 100, 255))
    
    def handle_submit():
        print(f"Login: {username.text} / {password.text}")
    
    password.on_submit = lambda _: handle_submit()
    
    running = True
    while running:
        for event in win.get_ui_events():
            if event.get("type") == "quit":
                running = False
            
            # Dispatch to inputs
            target = event.get("target")
            if target == "username":
                username.handle_event(event, win)
            elif target == "password":
                password.handle_event(event, win)
        
        # Build UI
        root = FlexBox(0, 0, "100%", "100%",
                       justify_content="center",
                       align_items="center")
        root.set_color((25, 25, 28, 255))
        
        form = FlexBox(0, 0, 350, "auto",
                       flex_direction="column",
                       gap=20,
                       padding=(40, 40, 40, 40))
        form.set_color((35, 35, 40, 255))
        form.set_radius(16)
        
        title = ResponsiveText(0, 0, "100%", "auto",
                              text="Sign In",
                              size=28,
                              color=(255, 255, 255, 255),
                              align="center")
        
        form.add_child(title)
        form.add_child(username)
        form.add_child(password)
        
        root.add_child(form)
        win.render([root.to_data()])
    
    win.close()

if __name__ == "__main__":
    main()
```

---

## Drawing with VectorGraphics

A simple chart using vector graphics:

```python
from sdl_gui.window.window import Window
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.vector_graphics import VectorGraphics
from sdl_gui.primitives.responsive_text import ResponsiveText
import math

def main():
    win = Window("Chart Example", 600, 400)
    
    # Sample data
    data = [30, 65, 45, 80, 55, 90, 70]
    
    running = True
    while running:
        for event in win.get_ui_events():
            if event.get("type") == "quit":
                running = False
        
        # Build chart
        root = FlexBox(0, 0, "100%", "100%",
                       flex_direction="column",
                       padding=(30, 30, 30, 30),
                       gap=20)
        root.set_color((25, 25, 28, 255))
        
        title = ResponsiveText(0, 0, "100%", 30,
                              text="Weekly Sales",
                              size=24,
                              color=(255, 255, 255, 255))
        root.add_child(title)
        
        # Chart area
        chart = VectorGraphics(0, 0, "100%", 250, cache_key="sales_chart")
        
        # Draw grid lines
        for i in range(5):
            y = i * 50 + 25
            chart.move_to(0, y)
            chart.line_to("100%", y)
        chart.stroke((50, 50, 55, 255), width=1)
        
        # Draw data line
        step = 540 // (len(data) - 1)  # Chart width / segments
        chart.move_to(0, 250 - (data[0] * 2.5))
        for i, val in enumerate(data[1:], 1):
            chart.line_to(i * step, 250 - (val * 2.5))
        chart.stroke((100, 180, 255, 255), width=3)
        
        # Draw data points
        for i, val in enumerate(data):
            chart.circle(i * step, 250 - (val * 2.5), 6)
        chart.fill((100, 180, 255, 255))
        
        root.add_child(chart)
        win.render([root.to_data()])
    
    win.close()

if __name__ == "__main__":
    main()
```

---

## Context Manager Syntax

Using `with` statements for cleaner hierarchy:

```python
from sdl_gui.window.window import Window
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.primitives.responsive_text import ResponsiveText

def main():
    win = Window("Context Manager", 800, 600)
    
    running = True
    while running:
        for event in win.get_ui_events():
            if event.get("type") == "quit":
                running = False
        
        # Build UI with context managers
        with Window as w:
            with FlexBox(0, 0, "100%", "100%", 
                        flex_direction="column", 
                        padding=20, gap=20) as root:
                root.set_color((25, 25, 28, 255))
                
                # Header - auto added to root
                Rectangle(0, 0, "100%", 60, (40, 40, 45, 255))
                
                # Content row
                with FlexBox(0, 0, "100%", "auto", 
                            flex_direction="row", gap=20) as row:
                    row.set_flex_grow(1)
                    
                    # Cards auto-added to row
                    for i in range(3):
                        with FlexBox(0, 0, "auto", "100%", padding=20) as card:
                            card.set_flex_grow(1)
                            card.set_color((35, 35, 40, 255))
                            card.set_radius(12)
                            
                            ResponsiveText(0, 0, "100%", "auto",
                                         text=f"Card {i+1}",
                                         color=(255, 255, 255, 255))
        
        win.render(w.get_root_display_list())
    
    win.close()

if __name__ == "__main__":
    main()
```

---

## More Examples

Check out the `examples/` directory in the repository for more complete demos:

- `demo_flexbox.py` - Comprehensive FlexBox showcase
- `layout_demo.py` - VBox/HBox layouts
- `demo_input.py` - Input field interactions
- `infinite_scroll_demo.py` - Scrollable lists
- `dashboard_charts_demo.py` - Complex charts and gauges
- `hover_animation_demo.py` - Animation effects
- `image_demo.py` - Image loading and display
