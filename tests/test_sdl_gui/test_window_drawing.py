import unittest
from unittest.mock import MagicMock, patch, call
import sys
import ctypes

# We will import Window, but we expect it to use real imports initially
# unless we mock sys.modules. However, patching afterwards is safer for checking calls.
# But Window __init__ calls sdl2.ext.init(), so we must control that too.

from sdl_gui.window.window import Window
from sdl_gui import core

class TestWindowDrawing(unittest.TestCase):
    def setUp(self):
        # Patch dependencies in the window module
        self.patchers = []
        
        self.mock_sdl2 = MagicMock()
        p1 = patch('sdl_gui.window.window.sdl2', self.mock_sdl2)
        self.patchers.append(p1)
        p1.start()
        
        self.mock_sdlgfx = MagicMock()
        p2 = patch('sdl_gui.window.window.sdlgfx', self.mock_sdlgfx)
        self.patchers.append(p2)
        p2.start()
        
        self.mock_ctypes = MagicMock()
        p3 = patch('sdl_gui.window.window.ctypes', self.mock_ctypes)
        self.patchers.append(p3)
        p3.start()
        
        self.mock_sdlttf = MagicMock()
        p4 = patch('sdl_gui.window.window.sdlttf', self.mock_sdlttf)
        self.patchers.append(p4)
        p4.start()

        self.window = Window("Test", 800, 600)
        # Mock renderer explicitly since __init__ might created a mocked one from mock_sdl2
        self.window.renderer = MagicMock()
        self.window.renderer.sdlrenderer = MagicMock()

    def tearDown(self):
        for p in reversed(self.patchers):
            p.stop()

    def test_draw_aa_rounded_box_calls(self):
        """Test that _draw_aa_rounded_box calls correct sdlgfx functions."""
        item = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_COLOR: (255, 0, 0, 255),
            core.KEY_RADIUS: 10,
            core.KEY_RECT: [0, 0, 100, 50]
        }
        
        rect = (10, 10, 100, 50)
        
        self.window._draw_rect_primitive(item, rect)
        
        # Verify sdlgfx calls
        self.mock_sdlgfx.roundedBoxColor.assert_called()
        self.assertEqual(self.mock_sdlgfx.aalineColor.call_count, 4)
        self.assertEqual(self.mock_sdlgfx.aacircleColor.call_count, 4)
        
        # ctypes/SDL clip calls
        # We mocked ctypes, so byref works (returns a mock)
        # We need to check if setClip was called.
        # Window calls sdl2.SDL_RenderSetClipRect
        self.mock_sdl2.SDL_RenderSetClipRect.assert_called()
        self.assertEqual(self.mock_sdl2.SDL_RenderSetClipRect.call_count, 5)

    def test_draw_aa_rounded_box_no_aa_if_radius_zero(self):
        """Test standard rect drawing if radius is 0."""
        item = {
            core.KEY_TYPE: core.TYPE_RECT,
            core.KEY_COLOR: (255, 0, 0, 255),
            core.KEY_RADIUS: 0
        }
        rect = (10, 10, 100, 50)
        
        self.window._draw_rect_primitive(item, rect)
        
        self.mock_sdlgfx.aacircleColor.assert_not_called()
        self.mock_sdlgfx.aalineColor.assert_not_called()

if __name__ == '__main__':
    unittest.main()
