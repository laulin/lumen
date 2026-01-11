import os
import shutil
import unittest

import sdl2
import sdl2.ext

from sdl_gui import core
from sdl_gui.window.window import Window


class TestVisualRendering(unittest.TestCase):
    OUTPUT_DIR = "tests/integration/output"
    BASELINE_DIR = "tests/integration/baselines"

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(cls.OUTPUT_DIR):
            os.makedirs(cls.OUTPUT_DIR)
        if not os.path.exists(cls.BASELINE_DIR):
            os.makedirs(cls.BASELINE_DIR)

        # Initialize SDL
        # Use dummy driver for headless testing if needed, though we want to test rendering.
        # Software renderer usually works fine off-screen with surfaces.
        # But Window usually opens a real window.
        # For integration test, we might tolerate a window flashing.
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    def test_aa_rect_rendering(self):
        """Render a scene with AA rects and compare with baseline."""
        filename = "aa_rect_test.bmp"
        output_path = os.path.join(self.OUTPUT_DIR, filename)
        baseline_path = os.path.join(self.BASELINE_DIR, filename)

        # Open Window (Force software renderer for dummy driver support)
        window = Window("Visual Test", 400, 300, renderer_flags=sdl2.SDL_RENDERER_SOFTWARE)

        # Content
        display_list = [
            {
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [0, 0, 400, 300], # Background
                core.KEY_COLOR: (0, 0, 0, 255)
            },
            {
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [50, 50, 200, 100],
                core.KEY_COLOR: (255, 0, 0, 255),
                core.KEY_RADIUS: 20
            },
            {
                core.KEY_TYPE: core.TYPE_RECT,
                core.KEY_RECT: [50, 160, 200, 100],
                core.KEY_COLOR: (0, 255, 0, 255),
                core.KEY_RADIUS: 20,
                core.KEY_BORDER_WIDTH: 2,
                core.KEY_BORDER_COLOR: (255, 255, 255, 255)
            }
        ]

        # Render
        window.render(display_list)

        # Save Screenshot
        window.save_screenshot(output_path)

        # Compare or Generate Baseline
        if not os.path.exists(baseline_path):
            print(f"Creating new baseline at {baseline_path}")
            shutil.copy(output_path, baseline_path)
        else:
            # Compare
            # Simple binary comparison? Or fuzzy?
            # Binary comparison for now. Rendering should be deterministic on same machine.
            with open(output_path, 'rb') as f1, open(baseline_path, 'rb') as f2:
                if f1.read() != f2.read():
                    self.fail(f"Visual regression detected! output {output_path} does not match baseline {baseline_path}")

        # Clean up SDL resources
        window.close()

if __name__ == '__main__':
    unittest.main()
