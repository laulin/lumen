"""
Unit tests for layout caching optimization in the Renderer.

Tests the layout cache for VBox and HBox elements.
"""

import unittest
from unittest.mock import MagicMock, patch

from sdl_gui import core


class TestLayoutCaching(unittest.TestCase):
    """Tests for layout caching in VBox and HBox."""

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

    def test_layout_cache_stats_initial_values(self):
        """Test that layout cache stats are initialized correctly."""
        stats = self.renderer.get_layout_cache_stats()
        
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)

    def test_layout_cache_stats_returns_copy(self):
        """Test that get_layout_cache_stats returns a copy."""
        stats1 = self.renderer.get_layout_cache_stats()
        stats1["hits"] = 999
        
        stats2 = self.renderer.get_layout_cache_stats()
        self.assertEqual(stats2["hits"], 0)

    def test_get_layout_cache_key(self):
        """Test that layout cache key generation works."""
        item = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_RECT: [0, 0, 100, 200],
            core.KEY_CHILDREN: [
                {core.KEY_TYPE: core.TYPE_RECT, core.KEY_RECT: [0, 0, 100, 50]}
            ]
        }
        parent_rect = (0, 0, 800, 600)
        
        key1 = self.renderer._get_layout_cache_key(item, parent_rect)
        key2 = self.renderer._get_layout_cache_key(item, parent_rect)
        
        # Same item = same key
        self.assertEqual(key1, key2)
        
        # Different parent rect = different key
        key3 = self.renderer._get_layout_cache_key(item, (0, 0, 400, 300))
        self.assertNotEqual(key1, key3)

    def test_layout_cache_key_changes_with_children(self):
        """Test that cache key changes when children change."""
        item1 = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_CHILDREN: [
                {core.KEY_TYPE: core.TYPE_RECT, "color": (255, 0, 0, 255)}
            ]
        }
        item2 = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_CHILDREN: [
                {core.KEY_TYPE: core.TYPE_RECT, "color": (0, 255, 0, 255)}  # Different
            ]
        }
        parent_rect = (0, 0, 800, 600)
        
        key1 = self.renderer._get_layout_cache_key(item1, parent_rect)
        key2 = self.renderer._get_layout_cache_key(item2, parent_rect)
        
        self.assertNotEqual(key1, key2)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_vbox_first_render_cache_miss(self, mock_clip):
        """Test that first VBox render is a cache miss."""
        item = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_RECT: [0, 0, 100, 200],
            core.KEY_CHILDREN: []
        }
        rect = (0, 0, 100, 200)
        
        self.renderer._render_vbox(item, rect)
        
        stats = self.renderer.get_layout_cache_stats()
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 0)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_vbox_second_render_cache_hit(self, mock_clip):
        """Test that second VBox render with same item is a cache hit."""
        item = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_RECT: [0, 0, 100, 200],
            core.KEY_CHILDREN: []
        }
        rect = (0, 0, 100, 200)
        
        self.renderer._render_vbox(item, rect)
        self.renderer._render_vbox(item, rect)
        
        stats = self.renderer.get_layout_cache_stats()
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 1)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_hbox_cache_behavior(self, mock_clip):
        """Test that HBox also uses layout cache."""
        item = {
            core.KEY_TYPE: core.TYPE_HBOX,
            core.KEY_RECT: [0, 0, 200, 100],
            core.KEY_CHILDREN: []
        }
        rect = (0, 0, 200, 100)
        
        self.renderer._render_hbox(item, rect)
        self.renderer._render_hbox(item, rect)
        
        stats = self.renderer.get_layout_cache_stats()
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 1)

    def test_layout_cache_invalidation_on_resize(self):
        """Test that layout cache is cleared on window resize."""
        # Compute a layout to populate cache
        item = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_CHILDREN: []
        }
        rect = (0, 0, 100, 200)
        
        with patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect'):
            self.renderer._render_vbox(item, rect)
        
        # Verify cache has entry
        self.assertEqual(len(self.renderer._layout_cache), 1)
        
        # Simulate resize by changing window size and calling render_list
        self.mock_window.size = (400, 300)  # Different size
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                with patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect'):
                    self.renderer.render_list([])
        
        # Cache should be cleared
        self.assertEqual(len(self.renderer._layout_cache), 0)


if __name__ == '__main__':
    unittest.main()
