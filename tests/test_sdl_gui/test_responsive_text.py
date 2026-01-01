import unittest

from sdl_gui import core
from sdl_gui.primitives.responsive_text import ResponsiveText


class TestResponsiveText(unittest.TestCase):
    def test_init_defaults(self):
        txt = ResponsiveText(x=0, y=0, width=100, height=20, text="Hello")
        self.assertEqual(txt.text, "Hello")
        self.assertEqual(txt.size, 16)
        self.assertEqual(txt.color, (0, 0, 0, 255))
        self.assertEqual(txt.align, "left")
        self.assertTrue(txt.wrap)
        self.assertTrue(txt.ellipsis)

    def test_to_data(self):
        txt = ResponsiveText(x=10, y=10, width=100, height=30,
                             text="Test",
                             size="50%",
                             color=(255, 0, 0, 255),
                             align="center",
                             id="txt1")
        data = txt.to_data()

        self.assertEqual(data[core.KEY_TYPE], core.TYPE_TEXT)
        self.assertEqual(data[core.KEY_TEXT], "Test")
        self.assertEqual(data[core.KEY_FONT_SIZE], "50%")
        self.assertEqual(data[core.KEY_COLOR], (255, 0, 0, 255))
        self.assertEqual(data[core.KEY_ALIGN], "center")
        self.assertTrue(data[core.KEY_WRAP])
        self.assertTrue(data[core.KEY_ELLIPSIS])
        self.assertEqual(data[core.KEY_ID], "txt1")
        self.assertEqual(data[core.KEY_RECT], [10, 10, 100, 30])

if __name__ == '__main__':
    unittest.main()
