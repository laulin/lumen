"""
Unit tests for viewport culling optimization in the Renderer.

Tests the _is_visible() helper method and culling statistics tracking.
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock

import sdl2
import sdl2.ext


class TestViewportCulling(unittest.TestCase):
    """Tests for viewport culling helper methods."""

    def setUp(self):
        """Set up a mock renderer for testing."""
        # We need to import the Renderer class
        from sdl_gui.window.renderer import Renderer
        
        # Mock SDL2 window
        self.mock_window = MagicMock()
        self.mock_window.size = (800, 600)
        
        # Patch SDL2 initialization
        with patch('sdl_gui.window.renderer.sdl2.ext.Renderer'):
            with patch('sdl_gui.rendering.text_renderer.sdlttf.TTF_Init'):
                self.renderer = Renderer(self.mock_window)

    def test_is_visible_fully_inside(self):
        """Test that a rect fully inside the viewport is visible."""
        viewport = (0, 0, 800, 600)
        rect = (100, 100, 200, 200)
        
        self.assertTrue(self.renderer._is_visible(rect, viewport))

    def test_is_visible_partially_overlapping_left(self):
        """Test that a rect partially overlapping the left edge is visible."""
        viewport = (100, 0, 700, 600)
        rect = (50, 100, 100, 200)  # Extends from x=50 to x=150
        
        self.assertTrue(self.renderer._is_visible(rect, viewport))

    def test_is_visible_partially_overlapping_right(self):
        """Test that a rect partially overlapping the right edge is visible."""
        viewport = (0, 0, 700, 600)
        rect = (650, 100, 100, 200)  # Extends from x=650 to x=750
        
        self.assertTrue(self.renderer._is_visible(rect, viewport))

    def test_is_visible_partially_overlapping_top(self):
        """Test that a rect partially overlapping the top edge is visible."""
        viewport = (0, 100, 800, 500)
        rect = (100, 50, 200, 100)  # Extends from y=50 to y=150
        
        self.assertTrue(self.renderer._is_visible(rect, viewport))

    def test_is_visible_partially_overlapping_bottom(self):
        """Test that a rect partially overlapping the bottom edge is visible."""
        viewport = (0, 0, 800, 500)
        rect = (100, 450, 200, 100)  # Extends from y=450 to y=550
        
        self.assertTrue(self.renderer._is_visible(rect, viewport))

    def test_is_visible_fully_outside_left(self):
        """Test that a rect fully outside to the left is not visible."""
        viewport = (100, 0, 700, 600)
        rect = (0, 100, 50, 200)  # Ends at x=50, viewport starts at x=100
        
        self.assertFalse(self.renderer._is_visible(rect, viewport))

    def test_is_visible_fully_outside_right(self):
        """Test that a rect fully outside to the right is not visible."""
        viewport = (0, 0, 700, 600)
        rect = (750, 100, 100, 200)  # Starts at x=750, viewport ends at x=700
        
        self.assertFalse(self.renderer._is_visible(rect, viewport))

    def test_is_visible_fully_outside_top(self):
        """Test that a rect fully outside above is not visible."""
        viewport = (0, 100, 800, 500)
        rect = (100, 0, 200, 50)  # Ends at y=50, viewport starts at y=100
        
        self.assertFalse(self.renderer._is_visible(rect, viewport))

    def test_is_visible_fully_outside_bottom(self):
        """Test that a rect fully outside below is not visible."""
        viewport = (0, 0, 800, 500)
        rect = (100, 600, 200, 100)  # Starts at y=600, viewport ends at y=500
        
        self.assertFalse(self.renderer._is_visible(rect, viewport))

    def test_is_visible_no_viewport(self):
        """Test that any rect is visible when no viewport is specified."""
        rect = (1000, 1000, 200, 200)  # Way outside window
        
        self.assertTrue(self.renderer._is_visible(rect, None))

    def test_is_visible_touching_edge(self):
        """Test that a rect exactly touching the viewport edge is not visible."""
        viewport = (100, 100, 600, 400)
        
        # Rect ends exactly where viewport starts (x)
        rect_left = (0, 200, 100, 100)  # Ends at x=100
        self.assertFalse(self.renderer._is_visible(rect_left, viewport))
        
        # Rect starts exactly where viewport ends (x)
        rect_right = (700, 200, 100, 100)  # Starts at x=700
        self.assertFalse(self.renderer._is_visible(rect_right, viewport))

    def test_culling_stats_initial_values(self):
        """Test that culling stats are initialized correctly."""
        stats = self.renderer.get_culling_stats()
        
        self.assertIn("rendered", stats)
        self.assertIn("skipped", stats)
        self.assertEqual(stats["rendered"], 0)
        self.assertEqual(stats["skipped"], 0)

    def test_culling_stats_returns_copy(self):
        """Test that get_culling_stats returns a copy, not the original."""
        stats1 = self.renderer.get_culling_stats()
        stats1["rendered"] = 999
        
        stats2 = self.renderer.get_culling_stats()
        self.assertEqual(stats2["rendered"], 0)


class TestViewportCullingIntegration(unittest.TestCase):
    """Integration tests for viewport culling in render methods."""

    def setUp(self):
        """Set up a mock renderer for testing."""
        from sdl_gui.window.renderer import Renderer
        
        self.mock_window = MagicMock()
        self.mock_window.size = (800, 600)
        
        with patch('sdl_gui.window.renderer.sdl2.ext.Renderer'):
            with patch('sdl_gui.rendering.text_renderer.sdlttf.TTF_Init'):
                self.renderer = Renderer(self.mock_window)

    def test_render_item_skips_invisible(self):
        """Test that _render_item skips items outside viewport."""
        from sdl_gui import core
        
        # Create an item outside the viewport
        item = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [0, 0, 100, 100],  # At 0,0 with size 100x100
            "color": (255, 0, 0, 255)
        }
        
        # Parent rect that places item at y=1000 (outside 600 height viewport)
        parent_rect = (0, 1000, 800, 600)
        viewport = (0, 0, 800, 600)
        
        with patch.object(self.renderer, '_draw_rect_primitive') as mock_draw:
            self.renderer._render_item(item, parent_rect, viewport)
            
            # Should not have drawn the rect
            mock_draw.assert_not_called()
            
            # Should have tracked as skipped
            stats = self.renderer.get_culling_stats()
            self.assertEqual(stats["skipped"], 1)
            self.assertEqual(stats["rendered"], 0)

    def test_render_item_renders_visible(self):
        """Test that _render_item renders items inside viewport."""
        from sdl_gui import core
        
        item = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_RECT: [100, 100, 200, 200],
            "color": (255, 0, 0, 255)
        }
        
        parent_rect = (0, 0, 800, 600)
        viewport = (0, 0, 800, 600)
        
        with patch.object(self.renderer, '_draw_rect_primitive') as mock_draw:
            self.renderer._render_item(item, parent_rect, viewport)
            
            mock_draw.assert_called_once()
            
            stats = self.renderer.get_culling_stats()
            self.assertEqual(stats["rendered"], 1)
            self.assertEqual(stats["skipped"], 0)


if __name__ == '__main__':
    unittest.main()
