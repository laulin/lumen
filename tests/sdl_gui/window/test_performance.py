"""
Unit tests for performance profiling and instrumentation in the Renderer.
"""

import unittest
from unittest.mock import MagicMock, patch


class TestPerformanceProfiling(unittest.TestCase):
    """Tests for performance profiling in Renderer."""

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

    def test_profiling_disabled_by_default(self):
        """Test that profiling is disabled by default."""
        self.assertFalse(self.renderer._perf_enabled)

    def test_enable_profiling(self):
        """Test enabling profiling."""
        self.renderer.enable_profiling(True)
        self.assertTrue(self.renderer._perf_enabled)
        
        self.renderer.enable_profiling(False)
        self.assertFalse(self.renderer._perf_enabled)

    def test_enable_profiling_resets_stats(self):
        """Test that enabling profiling resets stats."""
        self.renderer._perf_stats = {"old": 1.0}
        self.renderer._draw_call_count = 100
        
        self.renderer.enable_profiling(True)
        
        self.assertEqual(self.renderer._perf_stats, {})
        self.assertEqual(self.renderer._draw_call_count, 0)

    def test_get_perf_stats_structure(self):
        """Test that get_perf_stats returns correct structure."""
        stats = self.renderer.get_perf_stats()
        
        self.assertIn("timings", stats)
        self.assertIn("draw_calls", stats)
        self.assertIn("batch_stats", stats)
        self.assertIn("culling_stats", stats)
        self.assertIn("layout_cache_stats", stats)

    def test_get_perf_stats_returns_copy(self):
        """Test that get_perf_stats returns a copy."""
        stats1 = self.renderer.get_perf_stats()
        stats1["draw_calls"] = 999
        
        stats2 = self.renderer.get_perf_stats()
        self.assertEqual(stats2["draw_calls"], 0)

    def test_perf_timer_when_disabled(self):
        """Test that perf timers do nothing when disabled."""
        self.renderer._perf_enabled = False
        
        self.renderer._perf_start("test")
        self.renderer._perf_end("test")
        
        self.assertEqual(len(self.renderer._perf_stats), 0)

    def test_perf_timer_when_enabled(self):
        """Test that perf timers work when enabled."""
        self.renderer.enable_profiling(True)
        
        self.renderer._perf_start("test")
        # Simulate some work
        self.renderer._perf_end("test")
        
        self.assertIn("test", self.renderer._perf_stats)
        self.assertGreaterEqual(self.renderer._perf_stats["test"], 0)

    def test_batch_stats_initial(self):
        """Test initial batch stats values."""
        stats = self.renderer.get_perf_stats()
        
        self.assertEqual(stats["batch_stats"]["batched_rects"], 0)
        self.assertEqual(stats["batch_stats"]["saved_calls"], 0)


if __name__ == '__main__':
    unittest.main()
