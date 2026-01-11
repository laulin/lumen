
from typing import TYPE_CHECKING, Any, Dict, Tuple

from sdl_gui import core
from sdl_gui.layout_engine.node import FlexNode
from sdl_gui.layout_engine.style import (
    AlignItems,
    FlexDirection,
    FlexStyle,
    FlexWrap,
    JustifyContent,
)
from sdl_gui.rendering.primitive_renderer import PrimitiveRenderer

if TYPE_CHECKING:
    from sdl_gui.window.renderer import Renderer

class FlexRenderer:
    """
    Handles Flexbox layout calculation and rendering.
    """

    def __init__(self, renderer_proxy: 'Renderer', primitive_renderer: PrimitiveRenderer):
        self.renderer_proxy = renderer_proxy # To call render_item recursively
        self.primitive_renderer = primitive_renderer
        self._flex_layout_cache: Dict[Tuple, FlexNode] = {}

    def clear_cache(self):
        self._flex_layout_cache.clear()

    def render_flexbox(self, item: Dict[str, Any], rect: Tuple[int, int, int, int], viewport: Tuple[int, int, int, int] = None) -> None:
        """Render a FlexBox item by building a FlexNode tree and resolving layout."""
        x, y, w, h = rect

        item_hash = self.renderer_proxy._hash_item_cached(item)

        flex_cache_key = (item_hash, w, h, x, y)
        cached_node = self._flex_layout_cache.get(flex_cache_key)

        if cached_node is not None:
            root_node = cached_node
        else:
            # 1. Build Flex Tree
            root_node = self._build_flex_tree(item, w, h)

            # 2. Calculate Layout
            root_node.calculate_layout(w, h, x_offset=x, y_offset=y, force_size=True)

            # Cache the result
            self._flex_layout_cache[flex_cache_key] = root_node

        # 3. Render Background (if color/border exists)
        if item.get(core.KEY_COLOR) or item.get(core.KEY_BORDER_COLOR):
            self.primitive_renderer.draw_rect_primitive(item, rect)

        # 4. Render Children using calculated positions
        self._render_flex_node_children(root_node, item, viewport)

    def _build_flex_tree(self, item: Dict[str, Any], parent_w: int, parent_h: int) -> FlexNode:
        style = FlexStyle()

        # Map Flex Properties
        style.direction = FlexDirection(item.get(core.KEY_FLEX_DIRECTION, "row"))
        style.justify_content = JustifyContent(item.get(core.KEY_JUSTIFY_CONTENT, JustifyContent.FLEX_START.value))
        style.align_items = AlignItems(item.get(core.KEY_ALIGN_ITEMS, AlignItems.STRETCH.value))
        style.wrap = FlexWrap(item.get(core.KEY_FLEX_WRAP, "nowrap"))
        style.gap = item.get(core.KEY_GAP, 0)

        # Box Model
        style.grow = item.get(core.KEY_FLEX_GROW, 0.0)
        style.shrink = item.get(core.KEY_FLEX_SHRINK, 1.0)
        style.basis = item.get(core.KEY_FLEX_BASIS, "auto")
        style.padding = self._normalize_box_model(item.get(core.KEY_PADDING, (0, 0, 0, 0)))
        style.margin = self._normalize_box_model(item.get(core.KEY_MARGIN, (0, 0, 0, 0)))

        # Determine Explicit Size if any
        raw_rect = item.get(core.KEY_RECT)
        if raw_rect:
            if raw_rect[2] != "auto":
                 style.width = raw_rect[2]
            if raw_rect[3] != "auto":
                 style.height = raw_rect[3]

        node = FlexNode(style)
        node.original_item = item

        if item.get(core.KEY_TYPE) != core.TYPE_FLEXBOX:
            # Leaf node: provide a measure function
            # Use renderer_proxy helpers
            node.measure_func = lambda av_w, av_h, it=item: (
                self.renderer_proxy._measure_item_width(it, av_w, av_h),
                self.renderer_proxy._measure_item(it, av_w, av_h)
            )
        else:
            for child in item.get(core.KEY_CHILDREN, []):
                child_node = self._build_flex_tree(child, 0, 0)
                node.add_child(child_node)

        return node

    def _render_flex_node_children(self, node: FlexNode, item: Dict[str, Any], viewport: Tuple[int, int, int, int] = None):
        """Render flex node children with viewport culling."""
        # Get fresh children from the current item (not cached)
        children_items = item.get(core.KEY_CHILDREN, [])
        
        for i, child_node in enumerate(node.children):
            # Use fresh item from current display list if available
            if i < len(children_items):
                child_item = children_items[i]
            elif hasattr(child_node, 'original_item'):
                child_item = child_node.original_item
            else:
                continue

            cx, cy, cw, ch = child_node.layout_rect
            child_rect = (int(cx), int(cy), int(cw), int(ch))

            # Viewport culling check using renderer helper
            if not self.renderer_proxy._is_visible(child_rect, viewport):
                self.renderer_proxy._culling_stats["skipped"] += 1
                continue

            self.renderer_proxy._culling_stats["rendered"] += 1

            if child_item.get(core.KEY_TYPE) == core.TYPE_FLEXBOX:
                 self._render_flex_node_tree_pass(child_node, child_item, viewport)
            else:
                 # Call back to main renderer for dispatching leaf items
                 self.renderer_proxy.render_item_direct(child_item, (cx, cy, cw, ch))

    def _render_flex_node_tree_pass(self, node: FlexNode, item: Dict[str, Any], viewport: Tuple[int, int, int, int]):
         # Render the node itself (background)
         x, y, w, h = node.layout_rect
         rect = (int(x), int(y), int(w), int(h))

         if item.get(core.KEY_COLOR):
             self.primitive_renderer.draw_rect_primitive(item, rect)

         self._render_flex_node_children(node, item, viewport)

    def _normalize_box_model(self, val: Any) -> Tuple[int, int, int, int]:
        if isinstance(val, (int, float)):
            return (int(val), int(val), int(val), int(val))
        if isinstance(val, (list, tuple)):
            if len(val) == 2: return (int(val[0]), int(val[1]), int(val[0]), int(val[1]))
            if len(val) == 4: return (int(val[0]), int(val[1]), int(val[2]), int(val[3]))
        return (0, 0, 0, 0)
