import unittest
from sdl_gui import core
from sdl_gui.primitives.image import Image

class TestImageRadius(unittest.TestCase):
    def test_image_radius_to_data(self):
        # Default radius should be 0 and and not present in data
        img = Image(source="test.png", x=0, y=0, width=100, height=100)
        data = img.to_data()
        self.assertNotIn(core.KEY_RADIUS, data)
        self.assertEqual(data[core.KEY_TYPE], core.TYPE_IMAGE)

        # Explicit radius > 0 should be in data
        img_rounded = Image(source="test.png", x=0, y=0, width=100, height=100, radius=15)
        data_rounded = img_rounded.to_data()
        self.assertEqual(data_rounded[core.KEY_RADIUS], 15)

    def test_image_radius_setter(self):
        # Testing the generic setter mechanism from BasePrimitive
        img = Image(source="test.png", x=0, y=0, width=100, height=100)
        img.set_radius(25)
        data = img.to_data()
        self.assertEqual(data[core.KEY_RADIUS], 25)

if __name__ == "__main__":
    unittest.main()
