import unittest

from sdl_gui import core


class TestCoreProtocol(unittest.TestCase):
    def test_constants_defined(self):
        """Test that protocol constants are defined."""
        self.assertEqual(core.TYPE_LAYER, "layer")
        self.assertEqual(core.TYPE_RECT, "rect")
        self.assertEqual(core.TYPE_TEXT, "text")
        self.assertTrue(hasattr(core, "KEY_TYPE"))
        self.assertTrue(hasattr(core, "KEY_CHILDREN"))
        self.assertTrue(hasattr(core, "KEY_RECT"))
