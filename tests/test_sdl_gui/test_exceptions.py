import unittest
from sdl_gui.exceptions import SdlGuiError

class TestExceptions(unittest.TestCase):
    def test_sdl_gui_error_inheritance(self):
        """Test that SdlGuiError inherits from Exception."""
        err = SdlGuiError("Test error")
        self.assertIsInstance(err, Exception)
        self.assertEqual(str(err), "Test error")
