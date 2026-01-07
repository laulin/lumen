"""
Spatial index using quadtree for efficient spatial queries.

This module provides a quadtree-based spatial index for optimizing
rendering by efficiently querying elements within viewport regions.
"""

from typing import Any, Dict, List, Optional, Set, Tuple


class QuadTreeNode:
    """
    A node in the quadtree structure.
    
    Attributes:
        bounds: The bounding rectangle (x, y, width, height) of this node.
        max_items: Maximum items before subdividing.
        max_depth: Maximum tree depth.
        depth: Current depth of this node.
    """
    
    def __init__(
        self,
        bounds: Tuple[int, int, int, int],
        max_items: int = 8,
        max_depth: int = 6,
        depth: int = 0
    ):
        """
        Initialize a quadtree node.
        
        Args:
            bounds: The bounding rectangle (x, y, width, height).
            max_items: Maximum items before splitting.
            max_depth: Maximum tree depth.
            depth: Current depth of this node.
        """
        self.bounds = bounds
        self.max_items = max_items
        self.max_depth = max_depth
        self.depth = depth
        self.items: List[Tuple[str, Tuple[int, int, int, int]]] = []
        self.children: Optional[List["QuadTreeNode"]] = None
    
    def _subdivide(self) -> None:
        """Split this node into 4 quadrants."""
        x, y, w, h = self.bounds
        hw, hh = w // 2, h // 2
        
        self.children = [
            QuadTreeNode(
                (x, y, hw, hh),
                self.max_items,
                self.max_depth,
                self.depth + 1
            ),
            QuadTreeNode(
                (x + hw, y, w - hw, hh),
                self.max_items,
                self.max_depth,
                self.depth + 1
            ),
            QuadTreeNode(
                (x, y + hh, hw, h - hh),
                self.max_items,
                self.max_depth,
                self.depth + 1
            ),
            QuadTreeNode(
                (x + hw, y + hh, w - hw, h - hh),
                self.max_items,
                self.max_depth,
                self.depth + 1
            ),
        ]
        
        # Redistribute items to children
        for item_id, rect in self.items:
            for child in self.children:
                if child._intersects(rect):
                    child.insert(item_id, rect)
        
        self.items = []
    
    def _intersects(self, rect: Tuple[int, int, int, int]) -> bool:
        """Check if a rectangle intersects this node's bounds."""
        x, y, w, h = self.bounds
        rx, ry, rw, rh = rect
        
        return not (
            rx + rw <= x or rx >= x + w or
            ry + rh <= y or ry >= y + h
        )
    
    def insert(self, item_id: str, rect: Tuple[int, int, int, int]) -> bool:
        """
        Insert an item into the quadtree.
        
        Args:
            item_id: Unique identifier for the item.
            rect: Bounding rectangle (x, y, width, height).
            
        Returns:
            True if inserted successfully.
        """
        if not self._intersects(rect):
            return False
        
        if self.children is not None:
            for child in self.children:
                child.insert(item_id, rect)
            return True
        
        self.items.append((item_id, rect))
        
        if len(self.items) > self.max_items and self.depth < self.max_depth:
            self._subdivide()
        
        return True
    
    def query(
        self, rect: Tuple[int, int, int, int], result: Set[str]
    ) -> None:
        """
        Query items intersecting a rectangle.
        
        Args:
            rect: Query rectangle (x, y, width, height).
            result: Set to add matching item IDs to.
        """
        if not self._intersects(rect):
            return
        
        for item_id, item_rect in self.items:
            if self._rects_intersect(rect, item_rect):
                result.add(item_id)
        
        if self.children is not None:
            for child in self.children:
                child.query(rect, result)
    
    def _rects_intersect(
        self,
        a: Tuple[int, int, int, int],
        b: Tuple[int, int, int, int]
    ) -> bool:
        """Check if two rectangles intersect."""
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        
        return not (
            ax + aw <= bx or ax >= bx + bw or
            ay + ah <= by or ay >= by + bh
        )
    
    def remove(self, item_id: str) -> bool:
        """
        Remove an item from the quadtree.
        
        Args:
            item_id: The item ID to remove.
            
        Returns:
            True if the item was found and removed.
        """
        found = False
        self.items = [
            (iid, rect) for iid, rect in self.items if iid != item_id or not (found := True)
        ]
        
        if self.children is not None:
            for child in self.children:
                if child.remove(item_id):
                    found = True
        
        return found
    
    def clear(self) -> None:
        """Remove all items from this node and children."""
        self.items = []
        self.children = None


class SpatialIndex:
    """
    Spatial index for efficient viewport queries and dirty tracking.
    
    Uses a quadtree for O(log n) spatial queries and tracks dirty
    elements for incremental rendering optimization.
    """
    
    def __init__(
        self,
        bounds: Tuple[int, int, int, int] = (0, 0, 4096, 4096),
        max_depth: int = 6
    ):
        """
        Initialize the spatial index.
        
        Args:
            bounds: The world bounds (x, y, width, height).
            max_depth: Maximum quadtree depth.
        """
        self._bounds = bounds
        self._max_depth = max_depth
        self._root = QuadTreeNode(bounds, max_depth=max_depth)
        self._item_rects: Dict[str, Tuple[int, int, int, int]] = {}
        self._dirty_items: Set[str] = set()
        
        # Statistics
        self._stats: Dict[str, int] = {
            "inserts": 0,
            "removes": 0,
            "queries": 0,
            "dirty_marks": 0,
        }
    
    def insert(
        self, item_id: str, rect: Tuple[int, int, int, int]
    ) -> None:
        """
        Insert or update an item in the index.
        
        Args:
            item_id: Unique identifier for the item.
            rect: Bounding rectangle (x, y, width, height).
        """
        # Remove old entry if exists
        if item_id in self._item_rects:
            self._root.remove(item_id)
        
        self._item_rects[item_id] = rect
        self._root.insert(item_id, rect)
        self._stats["inserts"] += 1
    
    def remove(self, item_id: str) -> bool:
        """
        Remove an item from the index.
        
        Args:
            item_id: The item ID to remove.
            
        Returns:
            True if the item was found and removed.
        """
        if item_id in self._item_rects:
            del self._item_rects[item_id]
            self._dirty_items.discard(item_id)
            self._root.remove(item_id)
            self._stats["removes"] += 1
            return True
        return False
    
    def query(self, rect: Tuple[int, int, int, int]) -> Set[str]:
        """
        Query items intersecting a rectangle.
        
        Args:
            rect: Query rectangle (x, y, width, height).
            
        Returns:
            Set of item IDs intersecting the rectangle.
        """
        result: Set[str] = set()
        self._root.query(rect, result)
        self._stats["queries"] += 1
        return result
    
    def mark_dirty(self, item_id: str) -> None:
        """
        Mark an item as dirty (needs redraw).
        
        Args:
            item_id: The item ID to mark dirty.
        """
        if item_id in self._item_rects:
            self._dirty_items.add(item_id)
            self._stats["dirty_marks"] += 1
    
    def mark_all_dirty(self) -> None:
        """Mark all items as dirty."""
        self._dirty_items = set(self._item_rects.keys())
    
    def get_dirty_in_viewport(
        self, viewport: Tuple[int, int, int, int]
    ) -> Set[str]:
        """
        Get dirty items that are visible in the viewport.
        
        Args:
            viewport: The viewport rectangle.
            
        Returns:
            Set of dirty item IDs in the viewport.
        """
        visible = self.query(viewport)
        return visible & self._dirty_items
    
    def clear_dirty(self) -> None:
        """Clear all dirty flags."""
        self._dirty_items.clear()
    
    def get_item_rect(
        self, item_id: str
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the stored rectangle for an item.
        
        Args:
            item_id: The item ID.
            
        Returns:
            The rectangle or None if not found.
        """
        return self._item_rects.get(item_id)
    
    def clear(self) -> None:
        """Clear all items from the index."""
        self._root = QuadTreeNode(self._bounds, max_depth=self._max_depth)
        self._item_rects.clear()
        self._dirty_items.clear()
    
    def rebuild(self, bounds: Tuple[int, int, int, int] = None) -> None:
        """
        Rebuild the index with new bounds.
        
        Args:
            bounds: New bounds, or None to keep current.
        """
        if bounds is not None:
            self._bounds = bounds
        
        old_items = self._item_rects.copy()
        self.clear()
        
        for item_id, rect in old_items.items():
            self.insert(item_id, rect)
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about index operations.
        
        Returns:
            Dict with insert, remove, query, and dirty_marks counts.
        """
        return {
            **self._stats,
            "total_items": len(self._item_rects),
            "dirty_items": len(self._dirty_items),
        }
    
    def reset_stats(self) -> None:
        """Reset operation statistics."""
        self._stats = {
            "inserts": 0,
            "removes": 0,
            "queries": 0,
            "dirty_marks": 0,
        }
    
    def __len__(self) -> int:
        """Return the number of items in the index."""
        return len(self._item_rects)
    
    def __contains__(self, item_id: str) -> bool:
        """Check if an item is in the index."""
        return item_id in self._item_rects
