import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from sdl_gui.window.window import Window
from sdl_gui import core

class TestWindowUtils(unittest.TestCase):
    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2")
    def test_window_utils(self, mock_sdl2, mock_ext):
        """Test Window utility methods."""
        # Setup
        mock_renderer = MagicMock()
        mock_ext.Renderer.return_value = mock_renderer
        mock_window = MagicMock()
        mock_window.size = (800, 600)
        mock_ext.Window.return_value = mock_window
        
        # Initialize
        win = Window("Test", 800, 600)
        
        # 1. Test add_child and get_root_display_list
        child_mock = MagicMock()
        child_mock.to_data.return_value = {"type": "mock_child"}
        
        win.add_child(child_mock)
        
        display_list = win.get_root_display_list()
        self.assertEqual(len(display_list), 1)
        self.assertEqual(display_list[0]["type"], "mock_child")
        
        # 2. Test show
        win.show()
        mock_window.show.assert_called_once()
        
        # 3. Test save_screenshot
        # Mock surface creation and operations
        mock_surface = MagicMock()
        mock_surface_contents = MagicMock()
        mock_surface.contents = mock_surface_contents
        mock_sdl2.SDL_CreateRGBSurface.return_value = mock_surface
        
        win.save_screenshot("shot.bmp")
        
        mock_sdl2.SDL_CreateRGBSurface.assert_called_with(0, 800, 600, 32, ANY, ANY, ANY, ANY)
        mock_sdl2.SDL_RenderReadPixels.assert_called()
        mock_sdl2.SDL_SaveBMP.assert_called_with(mock_surface, b"shot.bmp")
        mock_sdl2.SDL_FreeSurface.assert_called_with(mock_surface)

    @patch("sdl_gui.window.window.sdl2.ext")
    @patch("sdl_gui.window.window.sdl2") 
    def test_context_manager(self, mock_sdl2, mock_ext):
        """Test Window context manager."""
        mock_ext.Renderer.return_value = MagicMock()
        mock_ext.Window.return_value = MagicMock()
        
        win = Window("Ctx", 100, 100)
        
        with patch("sdl_gui.context.push_parent") as mock_push, \
             patch("sdl_gui.context.pop_parent") as mock_pop:
             
             with win as w:
                 self.assertEqual(w, win)
                 mock_push.assert_called_with(win)
             
             mock_pop.assert_called()
