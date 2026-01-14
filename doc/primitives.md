# Primitives

Primitives are the basic building blocks for rendering content in Lumen. All primitives inherit from `BasePrimitive` and share common properties.

## Common Properties

All primitives support these base properties:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `x` | `int \| str` | required | X position (pixels or percentage) |
| `y` | `int \| str` | required | Y position (pixels or percentage) |
| `width` | `int \| str` | required | Width (pixels or percentage) |
| `height` | `int \| str` | required | Height (pixels or percentage) |
| `padding` | `tuple` | `(0,0,0,0)` | Inner spacing (top, right, bottom, left) |
| `margin` | `tuple` | `(0,0,0,0)` | Outer spacing (top, right, bottom, left) |
| `id` | `str` | `None` | Unique identifier for event targeting |
| `listen_events` | `list` | `[]` | Events this primitive responds to |

---

## Rectangle

A basic colored rectangle with optional rounded corners and border.

```python
from sdl_gui.primitives.rectangle import Rectangle

rect = Rectangle(
    x=0, y=0,
    width=200, height=100,
    color=(100, 150, 255, 255),
    radius=12,
    border_color=(255, 255, 255, 255),
    border_width=2
)
```

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `color` | `tuple` | required | RGBA background color |
| `radius` | `int` | `0` | Corner radius |
| `border_color` | `tuple` | `None` | RGBA border color |
| `border_width` | `int` | `0` | Border thickness |

---

## ResponsiveText

A text primitive with rich formatting support, text wrapping, and alignment.

```python
from sdl_gui.primitives.responsive_text import ResponsiveText

text = ResponsiveText(
    x=0, y=0,
    width="100%", height="auto",
    text="Hello, <b>Lumen</b>!",
    font="Roboto",
    size=18,
    color=(255, 255, 255, 255),
    align="center",
    wrap=True,
    markup=True
)
```

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `text` | `str` | required | Text content (supports markup) |
| `font` | `str` | `None` | Font family name |
| `size` | `int` | `16` | Font size in points |
| `color` | `tuple` | `(0,0,0,255)` | Text color |
| `align` | `str` | `"left"` | Alignment: `left`, `center`, `right` |
| `wrap` | `bool` | `True` | Enable text wrapping |
| `ellipsis` | `bool` | `True` | Show `...` for truncated text |
| `markup` | `bool` | `True` | Enable markup parsing |

### Markup Tags

When `markup=True`, the following tags are supported:

| Tag | Example | Description |
|-----|---------|-------------|
| `<b>` | `<b>bold</b>` | Bold text |
| `<i>` | `<i>italic</i>` | Italic text |
| `<u>` | `<u>underline</u>` | Underlined text |
| `<color>` | `<color=#FF0000>red</color>` | Colored text |

---

## Image

Display images from file paths or byte data.

```python
from sdl_gui.primitives.image import Image

img = Image(
    source="assets/logo.png",
    x=0, y=0,
    width=200, height=150,
    radius=12,
    scale_mode="fit"
)
```

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `source` | `str \| bytes \| callable` | required | Image path, data, or loader |
| `radius` | `int` | `0` | Corner radius for rounded images |
| `scale_mode` | `str` | `"fit"` | How to scale: `fit`, `fill`, `stretch` |

### Scale Modes

| Mode | Description |
|------|-------------|
| `fit` | Scale to fit within bounds, maintaining aspect ratio |
| `fill` | Scale to fill bounds, cropping if necessary |
| `stretch` | Stretch to fill bounds exactly |

---

## Input

A text input field with full editing support.

```python
from sdl_gui.primitives.input import Input

input_field = Input(
    x=0, y=0,
    width=300, height=40,
    text="",
    placeholder="Enter your name...",
    font="Roboto",
    size=16,
    color=(0, 0, 0, 255),
    background_color=(255, 255, 255, 255),
    border_color=(100, 100, 100, 255),
    border_width=1,
    radius=8,
    id="name_input"
)

# Callbacks
input_field.on_change = lambda text: print(f"Text changed: {text}")
input_field.on_submit = lambda text: print(f"Submitted: {text}")
```

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `text` | `str` | `""` | Current text value |
| `placeholder` | `str` | `""` | Placeholder text when empty |
| `font` | `str` | `None` | Font family |
| `size` | `int` | `16` | Font size |
| `color` | `tuple` | `(0,0,0,255)` | Text color |
| `background_color` | `tuple` | `None` | Background color (transparent) |
| `border_color` | `tuple` | `(0,0,0,255)` | Border color |
| `border_width` | `int` | `1` | Border thickness |
| `radius` | `int` | `0` | Corner radius |
| `max_length` | `int` | `None` | Max character limit |
| `multiline` | `bool` | `False` | Enable multiline input |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+A` | Select all |
| `Ctrl+C` | Copy selection |
| `Ctrl+V` | Paste |
| `Ctrl+X` | Cut selection |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` / `Ctrl+Y` | Redo |
| `Ctrl+Left/Right` | Move by word |
| `Shift+Arrows` | Extend selection |
| `Home` / `End` | Jump to start/end |

---

## VectorGraphics

Draw custom vector shapes with a fluent command API.

```python
from sdl_gui.primitives.vector_graphics import VectorGraphics

chart = VectorGraphics(
    x=0, y=0,
    width=400, height=200,
    cache_key="my_chart_v1"
)

# Draw a line chart
chart.move_to(0, 100)
chart.line_to(100, 50)
chart.line_to(200, 80)
chart.line_to(300, 30)
chart.stroke((100, 180, 255, 255), width=2)

# Draw a filled circle
chart.circle(350, 30, 8)
chart.fill((100, 180, 255, 255))
```

### Drawing Commands

| Command | Description |
|---------|-------------|
| `move_to(x, y)` | Move pen to position |
| `line_to(x, y)` | Draw line to position |
| `curve_to(cx1, cy1, cx2, cy2, x, y)` | Cubic bezier curve |
| `arc(x, y, r, start, end)` | Draw arc |
| `circle(x, y, r)` | Draw circle |
| `pie(x, y, r, start, end)` | Draw pie segment |
| `rect(x, y, w, h, r=0)` | Draw rectangle |
| `stroke(color, width=1)` | Stroke current path |
| `fill(color)` | Fill current path |
| `clear()` | Clear all commands |

### Percentage Coordinates

VectorGraphics supports percentage-based coordinates:

```python
chart.move_to("0%", "50%")
chart.line_to("100%", "50%")
chart.stroke((255, 255, 255, 255), width=1)
```

### Caching

Use `cache_key` to cache rendered graphics:

```python
# Static content - cache it
chart = VectorGraphics(x=0, y=0, width=200, height=100, cache_key="static_chart")

# Dynamic content - update cache key when content changes
chart.set_cache_key(f"chart_v{version}")
```

---

## Container

`Container` is a base class for primitives that can hold children. It enables context manager support.

```python
from sdl_gui.primitives.container import Container

# Context manager usage
with FlexBox(x=0, y=0, width="100%", height="100%") as parent:
    Rectangle(0, 0, 100, 50, (255, 0, 0, 255))  # Auto-added to parent
```

See [Layouts](layouts.md) for container implementations.
