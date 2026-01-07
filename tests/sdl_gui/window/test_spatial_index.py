"""
Unit tests for the SpatialIndex quadtree implementation.
"""

import unittest

from sdl_gui.window.spatial_index import SpatialIndex, QuadTreeNode


class TestQuadTreeNode(unittest.TestCase):
    """Tests for the QuadTreeNode class."""

    def test_node_creation(self):
        """Test that a node is created correctly."""
        node = QuadTreeNode((0, 0, 100, 100))
        self.assertEqual(node.bounds, (0, 0, 100, 100))
        self.assertEqual(node.depth, 0)
        self.assertEqual(len(node.items), 0)
        self.assertIsNone(node.children)

    def test_insert_single_item(self):
        """Test inserting a single item."""
        node = QuadTreeNode((0, 0, 100, 100))
        result = node.insert("item1", (10, 10, 20, 20))
        self.assertTrue(result)
        self.assertEqual(len(node.items), 1)

    def test_insert_outside_bounds_fails(self):
        """Test inserting an item outside bounds returns False."""
        node = QuadTreeNode((0, 0, 100, 100))
        result = node.insert("item1", (200, 200, 20, 20))
        self.assertFalse(result)
        self.assertEqual(len(node.items), 0)

    def test_subdivision(self):
        """Test that node subdivides when max items exceeded."""
        node = QuadTreeNode((0, 0, 100, 100), max_items=2, max_depth=4)
        node.insert("item1", (10, 10, 10, 10))
        node.insert("item2", (20, 20, 10, 10))
        self.assertIsNone(node.children)
        
        node.insert("item3", (30, 30, 10, 10))
        self.assertIsNotNone(node.children)
        self.assertEqual(len(node.children), 4)
        self.assertEqual(len(node.items), 0)

    def test_query_finds_items(self):
        """Test querying finds items in the query region."""
        node = QuadTreeNode((0, 0, 100, 100))
        node.insert("item1", (10, 10, 20, 20))
        node.insert("item2", (60, 60, 20, 20))
        
        result = set()
        node.query((5, 5, 30, 30), result)
        self.assertIn("item1", result)
        self.assertNotIn("item2", result)

    def test_query_with_subdivision(self):
        """Test querying works after subdivision."""
        node = QuadTreeNode((0, 0, 100, 100), max_items=2, max_depth=4)
        for i in range(5):
            node.insert(f"item{i}", (i * 15, i * 15, 10, 10))
        
        result = set()
        node.query((0, 0, 50, 50), result)
        self.assertIn("item0", result)
        self.assertIn("item1", result)
        self.assertIn("item2", result)

    def test_remove_item(self):
        """Test removing an item."""
        node = QuadTreeNode((0, 0, 100, 100))
        node.insert("item1", (10, 10, 20, 20))
        node.insert("item2", (60, 60, 20, 20))
        
        result = node.remove("item1")
        self.assertTrue(result)
        
        query_result = set()
        node.query((0, 0, 100, 100), query_result)
        self.assertNotIn("item1", query_result)
        self.assertIn("item2", query_result)

    def test_clear(self):
        """Test clearing the node."""
        node = QuadTreeNode((0, 0, 100, 100), max_items=2, max_depth=4)
        for i in range(5):
            node.insert(f"item{i}", (i * 15, i * 15, 10, 10))
        
        node.clear()
        self.assertEqual(len(node.items), 0)
        self.assertIsNone(node.children)


class TestSpatialIndex(unittest.TestCase):
    """Tests for the SpatialIndex class."""

    def test_creation(self):
        """Test index creation."""
        index = SpatialIndex()
        self.assertEqual(len(index), 0)

    def test_insert_and_query(self):
        """Test inserting and querying items."""
        index = SpatialIndex()
        index.insert("rect1", (10, 10, 50, 50))
        index.insert("rect2", (100, 100, 50, 50))
        
        result = index.query((0, 0, 80, 80))
        self.assertIn("rect1", result)
        self.assertNotIn("rect2", result)

    def test_update_item(self):
        """Test updating an item's position."""
        index = SpatialIndex()
        index.insert("rect1", (10, 10, 50, 50))
        
        result = index.query((0, 0, 80, 80))
        self.assertIn("rect1", result)
        
        index.insert("rect1", (200, 200, 50, 50))
        
        result = index.query((0, 0, 80, 80))
        self.assertNotIn("rect1", result)
        
        result = index.query((150, 150, 100, 100))
        self.assertIn("rect1", result)

    def test_remove(self):
        """Test removing items."""
        index = SpatialIndex()
        index.insert("rect1", (10, 10, 50, 50))
        
        self.assertIn("rect1", index)
        
        result = index.remove("rect1")
        self.assertTrue(result)
        self.assertNotIn("rect1", index)
        
        result = index.remove("nonexistent")
        self.assertFalse(result)

    def test_mark_dirty(self):
        """Test marking items as dirty."""
        index = SpatialIndex()
        index.insert("rect1", (10, 10, 50, 50))
        index.insert("rect2", (100, 100, 50, 50))
        
        index.mark_dirty("rect1")
        
        dirty = index.get_dirty_in_viewport((0, 0, 200, 200))
        self.assertIn("rect1", dirty)
        self.assertNotIn("rect2", dirty)

    def test_mark_all_dirty(self):
        """Test marking all items dirty."""
        index = SpatialIndex()
        index.insert("rect1", (10, 10, 50, 50))
        index.insert("rect2", (100, 100, 50, 50))
        
        index.mark_all_dirty()
        
        dirty = index.get_dirty_in_viewport((0, 0, 200, 200))
        self.assertIn("rect1", dirty)
        self.assertIn("rect2", dirty)

    def test_clear_dirty(self):
        """Test clearing dirty flags."""
        index = SpatialIndex()
        index.insert("rect1", (10, 10, 50, 50))
        index.mark_dirty("rect1")
        
        dirty = index.get_dirty_in_viewport((0, 0, 200, 200))
        self.assertEqual(len(dirty), 1)
        
        index.clear_dirty()
        
        dirty = index.get_dirty_in_viewport((0, 0, 200, 200))
        self.assertEqual(len(dirty), 0)

    def test_get_item_rect(self):
        """Test getting an item's stored rectangle."""
        index = SpatialIndex()
        rect = (10, 10, 50, 50)
        index.insert("rect1", rect)
        
        self.assertEqual(index.get_item_rect("rect1"), rect)
        self.assertIsNone(index.get_item_rect("nonexistent"))

    def test_clear(self):
        """Test clearing the index."""
        index = SpatialIndex()
        index.insert("rect1", (10, 10, 50, 50))
        index.mark_dirty("rect1")
        
        index.clear()
        
        self.assertEqual(len(index), 0)
        self.assertNotIn("rect1", index)

    def test_rebuild(self):
        """Test rebuilding the index."""
        index = SpatialIndex(bounds=(0, 0, 100, 100))
        index.insert("rect1", (10, 10, 50, 50))
        
        index.rebuild(bounds=(0, 0, 500, 500))
        
        self.assertEqual(len(index), 1)
        result = index.query((0, 0, 100, 100))
        self.assertIn("rect1", result)

    def test_stats(self):
        """Test stats tracking."""
        index = SpatialIndex()
        
        stats = index.get_stats()
        self.assertEqual(stats["inserts"], 0)
        self.assertEqual(stats["queries"], 0)
        
        index.insert("rect1", (10, 10, 50, 50))
        index.query((0, 0, 100, 100))
        
        stats = index.get_stats()
        self.assertEqual(stats["inserts"], 1)
        self.assertEqual(stats["queries"], 1)
        self.assertEqual(stats["total_items"], 1)

    def test_reset_stats(self):
        """Test resetting stats."""
        index = SpatialIndex()
        index.insert("rect1", (10, 10, 50, 50))
        
        index.reset_stats()
        
        stats = index.get_stats()
        self.assertEqual(stats["inserts"], 0)

    def test_bulk_insert_performance(self):
        """Test that bulk inserts complete in reasonable time."""
        import time
        
        index = SpatialIndex(bounds=(0, 0, 10000, 10000), max_depth=8)
        
        start = time.perf_counter()
        for i in range(1000):
            x = (i * 97) % 9900
            y = (i * 31) % 9900
            index.insert(f"item{i}", (x, y, 50, 50))
        elapsed = time.perf_counter() - start
        
        self.assertLess(elapsed, 1.0, f"1000 inserts took {elapsed:.2f}s")
        self.assertEqual(len(index), 1000)

    def test_query_performance(self):
        """Test that queries are fast."""
        import time
        
        index = SpatialIndex(bounds=(0, 0, 10000, 10000), max_depth=8)
        for i in range(1000):
            x = (i * 97) % 9900
            y = (i * 31) % 9900
            index.insert(f"item{i}", (x, y, 50, 50))
        
        start = time.perf_counter()
        for _ in range(1000):
            index.query((4000, 4000, 1000, 1000))
        elapsed = time.perf_counter() - start
        
        self.assertLess(elapsed, 0.5, f"1000 queries took {elapsed:.2f}s")

    def test_dirty_in_viewport_filters_correctly(self):
        """Test that get_dirty_in_viewport returns only visible dirty items."""
        index = SpatialIndex()
        index.insert("visible", (10, 10, 50, 50))
        index.insert("offscreen", (1000, 1000, 50, 50))
        
        index.mark_dirty("visible")
        index.mark_dirty("offscreen")
        
        dirty = index.get_dirty_in_viewport((0, 0, 200, 200))
        
        self.assertIn("visible", dirty)
        self.assertNotIn("offscreen", dirty)


if __name__ == '__main__':
    unittest.main()
