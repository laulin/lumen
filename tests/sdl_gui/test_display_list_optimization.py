
import unittest
from unittest.mock import MagicMock, patch
from sdl_gui import core
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.image import Image
from sdl_gui.primitives.input import Input
from sdl_gui.layouts.hbox import HBox
from sdl_gui.layouts.vbox import VBox

class TestDisplayListOptimization(unittest.TestCase):

    def test_rectangle_optimization(self):
        # Default rectangle
        rect = Rectangle(0, 0, 100, 100, (255, 0, 0, 255))
        data = rect.to_data()
        
        self.assertEqual(data[core.KEY_TYPE], core.TYPE_RECT)
        self.assertEqual(data[core.KEY_RECT], [0, 0, 100, 100])
        self.assertEqual(data["color"], (255, 0, 0, 255))
        
        # Keys that should NOT be present if default
        self.assertNotIn(core.KEY_RADIUS, data)
        self.assertNotIn(core.KEY_BORDER_COLOR, data)
        self.assertNotIn(core.KEY_BORDER_WIDTH, data)
        self.assertNotIn(core.KEY_PADDING, data)
        self.assertNotIn(core.KEY_MARGIN, data)
        self.assertNotIn(core.KEY_ID, data)
        self.assertNotIn(core.KEY_LISTEN_EVENTS, data)

        # Custom rectangle
        rect2 = Rectangle(10, 20, 50, 50, (0, 255, 0, 255), radius=5, border_width=2, border_color=(0,0,0,255), id="rect2")
        data2 = rect2.to_data()
        self.assertEqual(data2[core.KEY_RADIUS], 5)
        self.assertEqual(data2[core.KEY_BORDER_WIDTH], 2)
        self.assertEqual(data2[core.KEY_BORDER_COLOR], (0, 0, 0, 255))
        self.assertEqual(data2[core.KEY_ID], "rect2")

    def test_text_optimization(self):
        # Default text
        text = ResponsiveText(0, 0, 100, 100, "Hello")
        data = text.to_data()
        
        self.assertEqual(data[core.KEY_TEXT], "Hello")
        self.assertNotIn(core.KEY_FONT, data)
        self.assertNotIn(core.KEY_FONT_SIZE, data)
        self.assertNotIn(core.KEY_COLOR, data)
        self.assertNotIn(core.KEY_ALIGN, data)
        self.assertNotIn(core.KEY_WRAP, data)
        self.assertNotIn(core.KEY_ELLIPSIS, data)
        self.assertNotIn(core.KEY_MARKUP, data) # Default is True now

        # Custom text
        text2 = ResponsiveText(0,0,100,100, "MarkupOff", markup=False, size=20, color=(255,255,255,255), align="center")
        data2 = text2.to_data()
        self.assertIn(core.KEY_MARKUP, data2)
        self.assertFalse(data2[core.KEY_MARKUP])
        self.assertEqual(data2[core.KEY_FONT_SIZE], 20)
        self.assertEqual(data2[core.KEY_COLOR], (255,255,255,255))
        self.assertEqual(data2[core.KEY_ALIGN], "center")

    def test_image_optimization(self):
        img = Image("path/to/img", 0, 0, 100, 100)
        data = img.to_data()
        self.assertEqual(data[core.KEY_SOURCE], "path/to/img")
        self.assertNotIn(core.KEY_SCALE_MODE, data)

        img2 = Image("path", 0, 0, 100, 100, scale_mode="center")
        data2 = img2.to_data()
        self.assertEqual(data2[core.KEY_SCALE_MODE], "center")

    def test_input_optimization(self):
        inp = Input(0, 0, 100, 100)
        data = inp.to_data()
        
        self.assertNotIn("placeholder", data)
        self.assertNotIn(core.KEY_FONT_SIZE, data)
        self.assertNotIn(core.KEY_COLOR, data)
        self.assertNotIn("background_color", data)
        self.assertNotIn(core.KEY_BORDER_WIDTH, data)
        self.assertNotIn("multiline", data)
        self.assertNotIn("focused", data)

        inp2 = Input(0,0,100,100, text="test", placeholder="hint", multiline=True)
        inp2.focused = True
        data2 = inp2.to_data()
        self.assertEqual(data2["placeholder"], "hint")
        self.assertTrue(data2["multiline"])
        self.assertTrue(data2["focused"])

    def test_layout_optimization(self):
        hbox = HBox(0, 0, 100, 100)
        data = hbox.to_data()
        self.assertNotIn(core.KEY_CHILDREN, data)

        hbox.add_child(Rectangle(0,0,10,10,(0,0,0,255)))
        data2 = hbox.to_data()
        self.assertIn(core.KEY_CHILDREN, data2)
        self.assertEqual(len(data2[core.KEY_CHILDREN]), 1)

if __name__ == '__main__':
    unittest.main()
