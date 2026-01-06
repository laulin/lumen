"""
Benchmark tests for viewport culling optimization.

These tests verify that the culling mechanism provides measurable
performance improvements when rendering large numbers of elements.
"""

import unittest
from unittest.mock import MagicMock, patch

from sdl_gui import core


class TestViewportCullingBenchmark(unittest.TestCase):
    """Benchmark tests to validate culling performance improvements."""

    def setUp(self):
        """Set up a mock renderer for testing."""
        from sdl_gui.window.renderer import Renderer
        
        self.mock_window = MagicMock()
        self.mock_window.size = (800, 600)
        
        # Create a mock SDL renderer with all needed attributes
        self.mock_sdl_renderer = MagicMock()
        
        with patch('sdl_gui.window.renderer.sdl2.ext.Renderer') as mock_renderer_class:
            with patch('sdl_gui.window.renderer.sdlttf.TTF_Init'):
                mock_renderer_instance = MagicMock()
                mock_renderer_instance.sdlrenderer = self.mock_sdl_renderer
                mock_renderer_class.return_value = mock_renderer_instance
                
                self.renderer = Renderer(self.mock_window)

    def test_vbox_culling_logic(self):
        """
        Test that _render_vbox properly culls items outside viewport.
        
        With items starting at y=0 and viewport of 600px,
        items below y=600 should be skipped.
        """
        children = []
        for i in range(20):  # 20 items at 100px each = 2000px total
            children.append({
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [0, 0, 100, 100],
                "color": (100, 100, 100, 255)
            })
        
        item = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_RECT: [0, 0, 800, 2000],
            core.KEY_CHILDREN: children
        }
        
        rect = (0, 0, 800, 2000)
        viewport = (0, 0, 800, 600)  # Only 600px visible
        
        # Reset stats
        self.renderer._culling_stats = {"rendered": 0, "skipped": 0}
        
        with patch.object(self.renderer, '_render_element_at'):
            with patch.object(self.renderer, '_draw_rect_primitive'):
                self.renderer._render_vbox(item, rect, viewport)
        
        stats = self.renderer.get_culling_stats()
        
        # 6 items should be visible (600px / 100px), 14 should be skipped
        self.assertGreater(stats["skipped"], 0, f"Expected skipped items. Stats: {stats}")
        self.assertLess(stats["rendered"], 20, f"Expected less than 20 rendered. Stats: {stats}")
        
        # Calculate ratio
        total = stats["rendered"] + stats["skipped"]
        skip_ratio = stats["skipped"] / max(1, total)
        self.assertGreaterEqual(
            skip_ratio, 0.60,
            f"Expected at least 60% skip ratio, got {skip_ratio:.1%}. Stats: {stats}"
        )

    def test_hbox_culling_logic(self):
        """
        Test that _render_hbox properly culls items outside viewport.
        
        With items starting at x=0 and viewport of 800px,
        items beyond x=800 should be skipped.
        """
        children = []
        for i in range(20):  # 20 items at 100px each = 2000px total
            children.append({
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [0, 0, 100, 100],
                "color": (100, 100, 100, 255)
            })
        
        item = {
            core.KEY_TYPE: core.TYPE_HBOX,
            core.KEY_RECT: [0, 0, 2000, 600],
            core.KEY_CHILDREN: children
        }
        
        rect = (0, 0, 2000, 600)
        viewport = (0, 0, 800, 600)  # Only 800px visible
        
        self.renderer._culling_stats = {"rendered": 0, "skipped": 0}
        
        with patch.object(self.renderer, '_render_element_at'):
            with patch.object(self.renderer, '_draw_rect_primitive'):
                self.renderer._render_hbox(item, rect, viewport)
        
        stats = self.renderer.get_culling_stats()
        
        # 8 items should be visible (800px / 100px), 12 should be skipped
        self.assertGreater(stats["skipped"], 0, f"Expected skipped items. Stats: {stats}")
        self.assertLess(stats["rendered"], 20, f"Expected less than 20 rendered. Stats: {stats}")
        
        total = stats["rendered"] + stats["skipped"]
        skip_ratio = stats["skipped"] / max(1, total)
        self.assertGreaterEqual(
            skip_ratio, 0.50,
            f"Expected at least 50% skip ratio, got {skip_ratio:.1%}. Stats: {stats}"
        )

    def test_render_item_culling(self):
        """
        Test that _render_item culls items outside viewport.
        """
        item = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],
            "color": (255, 0, 0, 255)
        }
        
        # Reset stats
        self.renderer._culling_stats = {"rendered": 0, "skipped": 0}
        
        # Parent rect that places item at y=1000 (way outside 600px viewport)
        parent_rect = (0, 1000, 800, 600)
        viewport = (0, 0, 800, 600)
        
        with patch.object(self.renderer, '_draw_rect_primitive') as mock_draw:
            self.renderer._render_item(item, parent_rect, viewport)
            
            mock_draw.assert_not_called()
            
        stats = self.renderer.get_culling_stats()
        self.assertEqual(stats["skipped"], 1)
        self.assertEqual(stats["rendered"], 0)

    def test_all_visible_no_skipping(self):
        """
        Test that when all items fit in viewport, none are skipped.
        """
        children = []
        for i in range(5):  # 5 items at 50px = 250px, fits in 600px
            children.append({
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [0, 0, 100, 50],
                "color": (100, 100, 100, 255)
            })
        
        item = {
            core.KEY_TYPE: core.TYPE_VBOX,
            core.KEY_RECT: [0, 0, 800, 600],
            core.KEY_CHILDREN: children
        }
        
        rect = (0, 0, 800, 600)
        viewport = (0, 0, 800, 600)
        
        self.renderer._culling_stats = {"rendered": 0, "skipped": 0}
        
        with patch.object(self.renderer, '_render_element_at'):
            with patch.object(self.renderer, '_draw_rect_primitive'):
                self.renderer._render_vbox(item, rect, viewport)
        
        stats = self.renderer.get_culling_stats()
        
        # Nothing should be skipped
        self.assertEqual(stats["skipped"], 0, f"Expected no skipping. Stats: {stats}")
        self.assertEqual(stats["rendered"], 5, f"Expected 5 rendered. Stats: {stats}")

    def test_is_visible_helper_performance(self):
        """
        Test that _is_visible is fast even with many calls.
        """
        import time
        
        viewport = (0, 0, 800, 600)
        
        # Time 10000 visibility checks
        start = time.perf_counter()
        for i in range(10000):
            rect = (i % 1000, i % 800, 100, 100)
            self.renderer._is_visible(rect, viewport)
        elapsed = time.perf_counter() - start
        
        # Should complete in under 100ms (10000 calls)
        self.assertLess(elapsed, 0.1, f"_is_visible too slow: {elapsed*1000:.1f}ms for 10000 calls")


if __name__ == '__main__':
    unittest.main()
