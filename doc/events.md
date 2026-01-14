# Events

Lumen provides a comprehensive event system for handling user interactions.

## Event Loop

The main event loop uses `Window.get_ui_events()` to poll for events:

```python
from sdl_gui.window.window import Window
from sdl_gui import core

win = Window("My App", 800, 600)

running = True
while running:
    events = win.get_ui_events()
    
    for event in events:
        event_type = event.get("type")
        
        if event_type == core.EVENT_QUIT:
            running = False
        elif event_type == core.EVENT_CLICK:
            handle_click(event)
    
    win.render(display_list)
```

## Event Types

| Event | Constant | Description |
|-------|----------|-------------|
| Click | `core.EVENT_CLICK` | Mouse button pressed on element |
| Scroll | `core.EVENT_SCROLL` | Mouse wheel scrolled |
| Key Down | `core.EVENT_KEY_DOWN` | Keyboard key pressed |
| Text Input | `core.EVENT_TEXT_INPUT` | Text character entered |
| Focus | `core.EVENT_FOCUS` | Element gained focus |
| Blur | `core.EVENT_BLUR` | Element lost focus |
| Mouse Up | `core.EVENT_MOUSE_UP` | Mouse button released |
| Mouse Motion | `core.EVENT_MOUSE_MOTION` | Mouse moved |
| Hover Start | `core.EVENT_HOVER_START` | Mouse entered element |
| Hover End | `core.EVENT_HOVER_END` | Mouse left element |
| Tick | `core.EVENT_TICK` | Frame tick (always emitted) |
| Quit | `core.EVENT_QUIT` | Window close requested |
| Link Click | `core.EVENT_LINK_CLICK` | Hyperlink clicked |

---

## Subscribing to Events

Use `listen_events` to specify which events an element should receive:

```python
button = Rectangle(
    x=0, y=0,
    width=150, height=50,
    color=(100, 150, 255, 255),
    id="my_button",
    listen_events=["click", "hover_start", "hover_end"]
)
```

> [!IMPORTANT]
> Elements without an `id` cannot receive events. Always set an `id` for interactive elements.

---

## Event Data

Each event is a dictionary with type-specific data:

### Click Event

```python
{
    "type": "click",
    "target": "button_id",
    "local_x": 75,  # X relative to element
    "local_y": 25   # Y relative to element
}
```

### Scroll Event

```python
{
    "type": "scroll",
    "target": "scroll_container_id",
    "delta": -3,  # Scroll wheel delta (negative = down)
    "current_scroll_y": 120
}
```

### Key Down Event

```python
{
    "type": "key_down",
    "target": "input_id",
    "key_sym": 97,  # SDL key code (e.g., SDLK_a)
    "mod": 64       # Modifier keys (Ctrl, Shift, etc.)
}
```

### Text Input Event

```python
{
    "type": "text_input",
    "target": "input_id",
    "text": "a"  # The character(s) typed
}
```

### Focus/Blur Event

```python
{
    "type": "focus",  # or "blur"
    "target": "input_id"
}
```

### Mouse Motion Event

```python
{
    "type": "mouse_motion",
    "target": "element_id",
    "local_x": 45,
    "local_y": 30
}
```

### Tick Event

```python
{
    "type": "tick",
    "ticks": 123456  # SDL ticks (milliseconds since init)
}
```

---

## Handling Events

### Simple Click Handler

```python
def handle_events(events):
    for event in events:
        if event.get("type") == "click":
            target = event.get("target")
            
            if target == "submit_button":
                submit_form()
            elif target == "cancel_button":
                close_dialog()
```

### Event Dispatch to Components

For component-based architectures, dispatch events to the target:

```python
# Component registry
components = {
    "login_button": LoginButton(),
    "username_input": UsernameInput(),
}

def dispatch_events(events):
    for event in events:
        target = event.get("target")
        if target and target in components:
            components[target].handle_event(event)
```

### Input Component Event Handling

The `Input` primitive has built-in event handling:

```python
input_field = Input(
    x=0, y=0, width=300, height=40,
    id="username",
    text=""
)

# In event loop
for event in events:
    target = event.get("target")
    if target == "username":
        # Pass the event to the input component
        input_field.handle_event(event, context=window)
```

---

## Keyboard Modifiers

For `key_down` events, check modifiers:

```python
import sdl2

def handle_key(event):
    mod = event.get("mod", 0)
    key = event.get("key_sym")
    
    ctrl = bool(mod & sdl2.KMOD_CTRL)
    shift = bool(mod & sdl2.KMOD_SHIFT)
    alt = bool(mod & sdl2.KMOD_ALT)
    
    if ctrl and key == sdl2.SDLK_s:
        save_document()
    elif key == sdl2.SDLK_ESCAPE:
        close_dialog()
```

---

## Focus Management

Focus is managed automatically by Lumen:

1. Clicking on an element with `focus` in `listen_events` gives it focus
2. Previous focused element receives a `blur` event
3. New element receives a `focus` event

```python
input1 = Input(id="input1", ...)  # Automatically listens to focus/blur
input2 = Input(id="input2", ...)

# When user clicks input2:
# 1. input1 receives {"type": "blur", "target": "input1"}
# 2. input2 receives {"type": "focus", "target": "input2"}
```

---

## Best Practices

1. **Use descriptive IDs**: Make target identification clear
   ```python
   id="login_submit_button"  # Good
   id="btn1"                 # Bad
   ```

2. **Only listen to needed events**: Reduces overhead
   ```python
   listen_events=["click"]  # Just what you need
   ```

3. **Handle tick sparingly**: Runs every frame
   ```python
   # Use for animations, not heavy logic
   if event.get("type") == "tick":
       update_animation()
   ```

4. **Check target before processing**: Events may come from unexpected sources
   ```python
   if event.get("target") == expected_id:
       process_event(event)
   ```
