"""
Unit tests for dirty rectangles optimization in the Renderer.

Tests the display list diffing, dirty region tracking, and incremental rendering.
"""

import unittest
from unittest.mock import MagicMock, patch

from sdl_gui import core


class TestDirtyRectangles(unittest.TestCase):
    """Tests for dirty rectangles tracking methods."""

    def setUp(self):
        """Set up a mock renderer for testing."""
        from sdl_gui.window.renderer import Renderer
        
        self.mock_window = MagicMock()
        self.mock_window.size = (800, 600)
        
        self.mock_sdl_renderer = MagicMock()
        
        with patch('sdl_gui.window.renderer.sdl2.ext.Renderer') as mock_renderer_class:
            with patch('sdl_gui.rendering.text_renderer.sdlttf.TTF_Init'):
                mock_renderer_instance = MagicMock()
                mock_renderer_instance.sdlrenderer = self.mock_sdl_renderer
                mock_renderer_class.return_value = mock_renderer_instance
                
                self.renderer = Renderer(self.mock_window)

    def test_dirty_stats_initial_values(self):
        """Test that dirty stats are initialized correctly."""
        stats = self.renderer.get_dirty_stats()
        
        self.assertEqual(stats["full_renders"], 0)
        self.assertEqual(stats["partial_renders"], 0)
        self.assertEqual(stats["skipped_frames"], 0)

    def test_dirty_stats_returns_copy(self):
        """Test that get_dirty_stats returns a copy, not the original."""
        stats1 = self.renderer.get_dirty_stats()
        stats1["full_renders"] = 999
        
        stats2 = self.renderer.get_dirty_stats()
        self.assertEqual(stats2["full_renders"], 0)

    def test_set_incremental_mode(self):
        """Test enabling/disabling incremental mode."""
        # Initially off by default (for stability)
        self.assertFalse(self.renderer._incremental_mode)
        
        # Enable
        self.renderer.set_incremental_mode(True)
        self.assertTrue(self.renderer._incremental_mode)
        
        # Disable
        self.renderer.set_incremental_mode(False)
        self.assertFalse(self.renderer._incremental_mode)
        self.assertTrue(self.renderer._force_full_render)

    def test_mark_dirty_full(self):
        """Test marking entire window as dirty."""
        self.renderer._force_full_render = False  # Reset
        self.renderer.mark_dirty()
        self.assertTrue(self.renderer._force_full_render)

    def test_mark_dirty_region(self):
        """Test marking a specific region as dirty."""
        self.renderer._dirty_regions = []
        region = (100, 100, 200, 200)
        
        self.renderer.mark_dirty(region)
        
        self.assertIn(region, self.renderer._dirty_regions)

    def test_hash_item_same_items(self):
        """Test that identical items have same hash."""
        item1 = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }
        item2 = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }
        
        self.assertEqual(self.renderer._hash_item(item1), self.renderer._hash_item(item2))

    def test_hash_item_different_items(self):
        """Test that different items have different hash."""
        item1 = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }
        item2 = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (0, 255, 0, 255)  # Different color
        }
        
        self.assertNotEqual(self.renderer._hash_item(item1), self.renderer._hash_item(item2))

    def test_hash_item_ignores_children(self):
        """Test that children are ignored in hash computation."""
        item1 = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_RECT: [0, 0, 100, 100],
            core.KEY_CHILDREN: [{core.KEY_TYPE: core.TYPE_RECT}]
        }
        item2 = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_RECT: [0, 0, 100, 100],
            core.KEY_CHILDREN: [{core.KEY_TYPE: core.TYPE_TEXT}]  # Different child
        }
        
        # Hashes should be equal because children are excluded
        self.assertEqual(self.renderer._hash_item(item1), self.renderer._hash_item(item2))

    def test_hash_item_nested_dict(self):
        """Test that nested dicts don't cause TypeError (regression test)."""
        # This is a regression test for: TypeError: unhashable type: 'dict'
        item = {
            core.KEY_TYPE: "vector",
            core.KEY_RECT: [0, 0, 100, 100],
            "commands": [
                {"type": "line", "params": {"x1": 0, "y1": 0, "x2": 100, "y2": 100}},
                {"type": "circle", "params": {"cx": 50, "cy": 50, "r": 25}}
            ],
            "style": {"stroke": (255, 0, 0, 255), "fill": None}
        }
        
        # Should not raise TypeError
        hash_value = self.renderer._hash_item(item)
        self.assertIsInstance(hash_value, int)
        
        # Same item should produce same hash
        self.assertEqual(self.renderer._hash_item(item), self.renderer._hash_item(item))

    def test_compute_dirty_regions_identical_lists(self):
        """Test that identical lists produce no dirty regions."""
        item = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }
        
        parent_rect = (0, 0, 800, 600)
        
        dirty = self.renderer._compute_dirty_regions([item], [item], parent_rect)
        
        self.assertEqual(len(dirty), 0)

    def test_compute_dirty_regions_changed_item(self):
        """Test that a changed item creates dirty regions."""
        old_item = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }
        new_item = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (0, 255, 0, 255)  # Changed color
        }
        
        parent_rect = (0, 0, 800, 600)
        
        dirty = self.renderer._compute_dirty_regions([new_item], [old_item], parent_rect)
        
        self.assertGreater(len(dirty), 0)

    def test_compute_dirty_regions_different_lengths(self):
        """Test that different length lists produce dirty region covering parent."""
        item = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }
        
        parent_rect = (0, 0, 800, 600)
        
        dirty = self.renderer._compute_dirty_regions([item, item], [item], parent_rect)
        
        self.assertEqual(dirty, [parent_rect])

    def test_merge_dirty_regions_single(self):
        """Test that single region is returned as-is."""
        regions = [(100, 100, 200, 200)]
        
        merged = self.renderer._merge_dirty_regions(regions)
        
        self.assertEqual(merged, regions)

    def test_merge_dirty_regions_empty(self):
        """Test that empty list returns empty."""
        merged = self.renderer._merge_dirty_regions([])
        
        self.assertEqual(merged, [])

    def test_merge_dirty_regions_overlapping(self):
        """Test merging of overlapping regions."""
        regions = [
            (100, 100, 100, 100),  # 100-200, 100-200
            (150, 150, 100, 100)   # 150-250, 150-250
        ]
        
        merged = self.renderer._merge_dirty_regions(regions)
        
        # Should be merged into bounding box
        self.assertEqual(len(merged), 1)
        # Bounding box: 100-250, 100-250 = (100, 100, 150, 150)
        self.assertEqual(merged[0], (100, 100, 150, 150))


class TestDirtyRectanglesIntegration(unittest.TestCase):
    """Integration tests for dirty rectangles in render methods."""

    def setUp(self):
        """Set up a mock renderer for testing."""
        from sdl_gui.window.renderer import Renderer
        
        self.mock_window = MagicMock()
        self.mock_window.size = (800, 600)
        
        self.mock_sdl_renderer = MagicMock()
        
        with patch('sdl_gui.window.renderer.sdl2.ext.Renderer') as mock_renderer_class:
            with patch('sdl_gui.rendering.text_renderer.sdlttf.TTF_Init'):
                mock_renderer_instance = MagicMock()
                mock_renderer_instance.sdlrenderer = self.mock_sdl_renderer
                mock_renderer_class.return_value = mock_renderer_instance
                
                self.renderer = Renderer(self.mock_window)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_first_render_is_full(self, mock_clip):
        """Test that first render is always a full render."""
        display_list = [{
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }]
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                self.renderer.render_list(display_list)
        
        stats = self.renderer.get_dirty_stats()
        self.assertEqual(stats["full_renders"], 1)
        self.assertEqual(stats["partial_renders"], 0)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_identical_second_render_skipped(self, mock_clip):
        """Test that identical display list on second render is skipped."""
        display_list = [{
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }]
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                # First render (full)
                self.renderer.render_list(display_list)
                
                # Second render with identical list (should skip)
                self.renderer.render_list(display_list)
        
        stats = self.renderer.get_dirty_stats()
        self.assertEqual(stats["full_renders"], 1)
        self.assertEqual(stats["skipped_frames"], 1)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_changed_list_triggers_partial(self, mock_clip):
        """Test that changed display list triggers partial render."""
        display_list1 = [{
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }]
        display_list2 = [{
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (0, 255, 0, 255)  # Changed color
        }]
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                self.renderer.render_list(display_list1)
                self.renderer.render_list(display_list2)
        
        stats = self.renderer.get_dirty_stats()
        self.assertEqual(stats["full_renders"], 1)
        self.assertEqual(stats["partial_renders"], 1)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_force_full_ignores_incremental(self, mock_clip):
        """Test that force_full=True forces a full render."""
        display_list = [{
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }]
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                self.renderer.render_list(display_list)
                self.renderer.render_list(display_list, force_full=True)
        
        stats = self.renderer.get_dirty_stats()
        self.assertEqual(stats["full_renders"], 2)


if __name__ == '__main__':
    unittest.main()
