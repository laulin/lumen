import unittest
import subprocess
import time
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from sdl_gui.debug.client import DebugClient

class TestFlexboxIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the app in a separate process
        env = os.environ.copy()
        env["SDL_VIDEODRIVER"] = "dummy" # Headless mode for CI
        cls.process = subprocess.Popen(
            [sys.executable, "tests/integration/app.py"],
            env=env
        )
        # Wait for server to start and app to render first frame
        time.sleep(2.0)
        cls.client = DebugClient()
        cls.client.connect()

    @classmethod
    def tearDownClass(cls):
        try:
            # Tell the app to quit gracefully via debug API
            cls.client.quit()
        except:
            pass
        finally:
            cls.client.close()
            # If it hasn't quit yet, terminate it
            time.sleep(0.5)
            if cls.process.poll() is None:
                cls.process.terminate()
                cls.process.wait()

    def test_px_red_box_position(self):
        """Red box should be at (0, 0) as it is the first item in the first row."""
        # Check center of red box: (25, 25)
        resp = self.client.get_pixel(25, 25)
        self.assertEqual(resp["status"], "ok", f"Debug API error: {resp.get('message')}")
        self.assertEqual(tuple(resp["data"]), (255, 0, 0, 255), "Red box not found at expected position")

    def test_px_green_box_position(self):
        """Green box should be at the right edge due to space-between."""
        # Row 1 is 800px wide. Green box is 50px wide. 
        # With space-between and 2 items, they are at extreme ends.
        # Green box X should be 800 - 50 = 750.
        # Center of green box: X=775, Y=25
        resp = self.client.get_pixel(775, 25)
        self.assertEqual(resp["status"], "ok", f"Debug API error: {resp.get('message')}")
        self.assertEqual(tuple(resp["data"]), (0, 255, 0, 255), "Green box not found at expected position")

    def test_px_blue_box_position(self):
        """Blue box should be centered in the middle of Row 2."""
        # Row 1 (0-100), Row 2 (100-300).
        # Blue box (100x100) centered vertically and horizontally in Row 2.
        # Horizontal center: 800/2 = 400.
        # Vertical center: 100 + 200/2 = 200.
        resp = self.client.get_pixel(400, 200)
        self.assertEqual(resp["status"], "ok", f"Debug API error: {resp.get('message')}")
        self.assertEqual(tuple(resp["data"]), (0, 0, 255, 255), "Blue box not found at expected position")

    def test_px_yellow_box_position(self):
        """Yellow box should be at bottom-right of Row 3."""
        # Row 1 (0-100), Row 2 (100-300), Row 3 (300-400).
        # Row 3 is 100px high. Yellow box is 40x40.
        # justify-content: flex_end -> X = 800 - 40 = 760.
        # align-items: flex_end -> Y = 300 + (100 - 40) = 360.
        # Center of yellow box: X=780, Y=380.
        resp = self.client.get_pixel(780, 380)
        self.assertEqual(resp["status"], "ok", f"Debug API error: {resp.get('message')}")
        self.assertEqual(tuple(resp["data"]), (255, 255, 0, 255), "Yellow box not found at expected position")

    def test_px_background(self):
        """Check that background color is correct between boxes."""
        # Check a pixel that should be background (e.g. 400, 50 - between red and green)
        resp = self.client.get_pixel(400, 50)
        self.assertEqual(resp["status"], "ok")
        # Row 1 color is (30, 30, 30, 255)
        self.assertEqual(tuple(resp["data"]), (30, 30, 30, 255), "Background color mismatch in Row 1")

if __name__ == "__main__":
    unittest.main()
