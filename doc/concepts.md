# Core Concepts

This document explains the fundamental concepts used throughout the Lumen library.

## Positioning

All primitives accept `x` and `y` parameters that define their position relative to their parent container.

### Absolute Values (pixels)
```python
Rectangle(x=10, y=20, width=100, height=50, color=(255, 0, 0, 255))
```

### Percentage Values
```python
Rectangle(x="10%", y="20%", width="80%", height="50%", color=(255, 0, 0, 255))
```

Percentages are calculated relative to the parent container's **content area** (after padding is applied).

## Sizing

| Value Type | Description | Example |
|------------|-------------|---------|
| `int` | Fixed size in pixels | `width=200` |
| `str` (percentage) | Percentage of parent | `width="50%"` |
| `"100%"` | Fill parent | `width="100%"` |
| `"auto"` | Size to content (FlexBox) | `height="auto"` |

## Padding

Padding creates space **inside** a container, between its edges and its content.

```
┌──────────────────────────────────┐
│           padding-top            │
│   ┌──────────────────────────┐   │
│ p │                          │ p │
│ a │        Content           │ a │
│ d │                          │ d │
│ - │                          │ - │
│ l │                          │ r │
│ e │                          │ i │
│ f │                          │ g │
│ t │                          │ h │
│   └──────────────────────────┘ t │
│          padding-bottom          │
└──────────────────────────────────┘
```

### Syntax Options

```python
# Single value: applies to all sides
padding=10                      # (10, 10, 10, 10)

# Two values: (vertical, horizontal)
padding=(10, 20)                # (10, 20, 10, 20)

# Four values: (top, right, bottom, left)
padding=(10, 20, 15, 25)        # explicit
```

## Margin

Margin creates space **outside** a container, between it and its siblings or parent.

```
          margin-top
        ┌──────────┐
margin  │ Element  │  margin
-left   │          │  -right
        └──────────┘
         margin-bottom
```

The margin syntax is identical to padding:

```python
margin=10                       # all sides
margin=(10, 20)                 # (vertical, horizontal)
margin=(10, 20, 15, 25)         # (top, right, bottom, left)
```

## Colors

Colors are specified as RGBA tuples with values from 0-255:

```python
color = (red, green, blue, alpha)

# Examples
red = (255, 0, 0, 255)          # fully opaque red
blue_50 = (0, 0, 255, 128)      # 50% transparent blue
white = (255, 255, 255, 255)
transparent = (0, 0, 0, 0)
```

> [!TIP]
> If you provide only 3 values (RGB), Lumen will automatically add `255` for alpha.

## Borders

Many primitives support borders:

| Property | Type | Description |
|----------|------|-------------|
| `border_width` | `int` | Border thickness in pixels |
| `border_color` | `tuple` | RGBA color tuple |
| `radius` | `int` | Corner radius for rounded borders |

```python
Rectangle(
    x=0, y=0, width=200, height=100,
    color=(50, 50, 50, 255),
    border_width=2,
    border_color=(100, 180, 255, 255),
    radius=12
)
```

## Fluent API

All primitives support a fluent setter API for style properties:

```python
box = FlexBox(x=0, y=0, width="100%", height=100)
box.set_color((30, 30, 35, 255))    \
   .set_radius(12)                   \
   .set_border_width(1)              \
   .set_border_color((100, 180, 255, 255))
```

### Available Setters

| Method | Description |
|--------|-------------|
| `set_color()` / `set_background_color()` | Background color |
| `set_radius()` | Corner radius |
| `set_border_width()` | Border thickness |
| `set_border_color()` | Border color |
| `set_padding()` | Inner spacing |
| `set_margin()` | Outer spacing |
| `set_flex_grow()` | Flexbox grow factor |
| `set_flex_shrink()` | Flexbox shrink factor |
| `set_flex_basis()` | Flexbox base size |
| `set_gap()` | Gap between children |

## Display List Architecture

Lumen uses a **display list** architecture:

1. **Build Phase**: You construct a tree of primitives
2. **Serialize Phase**: Call `to_data()` to convert to a dictionary structure
3. **Render Phase**: Pass the display list to `Window.render()`

```python
# Build
root = VBox(x=0, y=0, width="100%", height="100%")
root.add_child(Rectangle(0, 0, "100%", 50, (255, 0, 0, 255)))

# Serialize & Render
display_list = [root.to_data()]
window.render(display_list)
```

This decouples UI construction from rendering, enabling:
- Efficient diffing and caching
- Debug introspection
- Serialization for testing

## Context Managers

Containers support Python's `with` statement for implicit child registration:

```python
with FlexBox(x=0, y=0, width="100%", height="100%") as root:
    Rectangle(0, 0, 100, 50, (255, 0, 0, 255))  # auto-added to root
    ResponsiveText(0, 0, "100%", 30, text="Hello")  # auto-added to root
```

This creates cleaner, more readable code for complex hierarchies.
