"""
Unit tests for spatial index integration in the Renderer.
"""

import unittest
from unittest.mock import MagicMock, patch

from sdl_gui import core


class TestSpatialIndexIntegration(unittest.TestCase):
    """Tests for spatial index integration in Renderer."""

    def setUp(self):
        """Set up a mock renderer for testing."""
        from sdl_gui.window.renderer import Renderer
        
        self.mock_window = MagicMock()
        self.mock_window.size = (800, 600)
        
        self.mock_sdl_renderer = MagicMock()
        
        with patch('sdl_gui.window.renderer.sdl2.ext.Renderer') as mock_renderer_class:
            with patch('sdl_gui.window.renderer.sdlttf.TTF_Init'):
                mock_renderer_instance = MagicMock()
                mock_renderer_instance.sdlrenderer = self.mock_sdl_renderer
                mock_renderer_class.return_value = mock_renderer_instance
                
                self.renderer = Renderer(self.mock_window)

    def test_spatial_index_initialized(self):
        """Test that spatial index is initialized in renderer."""
        self.assertIsNotNone(self.renderer._spatial_index)

    def test_get_spatial_stats_initial(self):
        """Test initial spatial stats values."""
        stats = self.renderer.get_spatial_stats()
        
        self.assertEqual(stats["inserts"], 0)
        self.assertEqual(stats["queries"], 0)
        self.assertEqual(stats["total_items"], 0)

    def test_get_perf_stats_includes_spatial_stats(self):
        """Test that get_perf_stats includes spatial index stats."""
        stats = self.renderer.get_perf_stats()
        
        self.assertIn("spatial_index_stats", stats)
        self.assertEqual(stats["spatial_index_stats"]["inserts"], 0)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_render_list_populates_spatial_index(self, mock_clip):
        """Test that render_list populates the spatial index."""
        display_list = [
            {
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [10, 10, 50, 50],
                "color": (255, 0, 0, 255)
            },
            {
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [100, 100, 50, 50],
                "color": (0, 255, 0, 255)
            }
        ]
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                self.renderer.render_list(display_list)
        
        stats = self.renderer.get_spatial_stats()
        self.assertEqual(stats["total_items"], 2)
        self.assertEqual(stats["inserts"], 2)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_render_list_indexes_children(self, mock_clip):
        """Test that render_list indexes nested children."""
        display_list = [
            {
                core.KEY_TYPE: core.TYPE_LAYER,
                core.KEY_RECT: [0, 0, 800, 600],
                core.KEY_CHILDREN: [
                    {
                        core.KEY_TYPE: core.TYPE_RECT,
                        core.KEY_RECT: [10, 10, 50, 50],
                    },
                    {
                        core.KEY_TYPE: core.TYPE_RECT,
                        core.KEY_RECT: [100, 100, 50, 50],
                    }
                ]
            }
        ]
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                self.renderer.render_list(display_list)
        
        stats = self.renderer.get_spatial_stats()
        # 1 layer + 2 rects = 3 items
        self.assertEqual(stats["total_items"], 3)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_spatial_index_clears_between_frames(self, mock_clip):
        """Test that spatial index is cleared between render frames."""
        display_list = [
            {
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [10, 10, 50, 50],
            }
        ]
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                self.renderer.render_list(display_list)
                self.renderer.render_list(display_list)
        
        stats = self.renderer.get_spatial_stats()
        # Should still have 1 item, not 2
        self.assertEqual(stats["total_items"], 1)
        # But inserts should be 2 (one per frame)
        self.assertEqual(stats["inserts"], 2)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_spatial_index_rebuilds_on_resize(self, mock_clip):
        """Test that spatial index rebuilds when window is resized."""
        display_list = [
            {
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [10, 10, 50, 50],
            }
        ]
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                self.renderer.render_list(display_list)
                
                # Change window size
                self.mock_window.size = (1024, 768)
                
                self.renderer.render_list(display_list)
        
        # Index should still have 1 item after rebuild
        stats = self.renderer.get_spatial_stats()
        self.assertEqual(stats["total_items"], 1)

    def test_spatial_query_viewport(self):
        """Test querying visible items in viewport."""
        # Insert items directly for testing
        self.renderer._spatial_index.insert("item1", (10, 10, 50, 50))
        self.renderer._spatial_index.insert("item2", (1000, 1000, 50, 50))
        
        # Query viewport
        visible = self.renderer._spatial_index.query((0, 0, 800, 600))
        
        self.assertIn("item1", visible)
        self.assertNotIn("item2", visible)


class TestSpatialIndexPerformance(unittest.TestCase):
    """Performance tests for spatial index in Renderer."""

    def setUp(self):
        """Set up a mock renderer for testing."""
        from sdl_gui.window.renderer import Renderer
        
        self.mock_window = MagicMock()
        self.mock_window.size = (800, 600)
        
        self.mock_sdl_renderer = MagicMock()
        
        with patch('sdl_gui.window.renderer.sdl2.ext.Renderer') as mock_renderer_class:
            with patch('sdl_gui.window.renderer.sdlttf.TTF_Init'):
                mock_renderer_instance = MagicMock()
                mock_renderer_instance.sdlrenderer = self.mock_sdl_renderer
                mock_renderer_class.return_value = mock_renderer_instance
                
                self.renderer = Renderer(self.mock_window)

    @patch('sdl_gui.window.renderer.sdl2.SDL_RenderSetClipRect')
    def test_build_spatial_index_performance(self, mock_clip):
        """Test that building spatial index is fast for many items."""
        import time
        
        # Create display list with many items
        children = []
        for i in range(100):
            children.append({
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [(i % 10) * 80, (i // 10) * 60, 70, 50],
                "color": (100, 100, 100, 255)
            })
        
        display_list = [
            {
                core.KEY_TYPE: core.TYPE_VBOX,
                core.KEY_RECT: [0, 0, 800, 600],
                core.KEY_CHILDREN: children
            }
        ]
        
        with patch.object(self.renderer, '_render_item'):
            with patch.object(self.renderer, '_flush_render_queue'):
                start = time.perf_counter()
                for _ in range(10):
                    self.renderer.render_list(display_list)
                elapsed = time.perf_counter() - start
        
        # 10 frames with 101 items each should be under 100ms
        self.assertLess(elapsed, 0.1, f"Build took {elapsed*1000:.1f}ms for 10 frames")

    def test_spatial_query_performance(self):
        """Test that spatial queries are fast."""
        import time
        
        # Insert many items
        for i in range(500):
            x = (i * 97) % 1500
            y = (i * 31) % 1500
            self.renderer._spatial_index.insert(f"item{i}", (x, y, 50, 50))
        
        # Time many queries
        start = time.perf_counter()
        for _ in range(1000):
            self.renderer._spatial_index.query((200, 200, 400, 300))
        elapsed = time.perf_counter() - start
        
        # 1000 queries should be under 100ms
        self.assertLess(elapsed, 0.1, f"1000 queries took {elapsed*1000:.1f}ms")


if __name__ == '__main__':
    unittest.main()
