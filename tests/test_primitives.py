
import unittest

from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive


class MockPrimitive(BasePrimitive):
    def to_data(self):
        return super().to_data()

class TestBasePrimitiveSetters(unittest.TestCase):
    def setUp(self):
        self.prim = MockPrimitive(0, 0, 100, 100)

    def test_generic_setter_valid_single_value(self):
        self.prim.set_radius(10)
        self.assertEqual(self.prim.extra[core.KEY_RADIUS], 10)

    def test_generic_setter_valid_tuple_value(self):
        # Color typically passed as expanded args in previous plan,
        # but generic setter handles *args.
        # If we call set_border_color(1, 2, 3, 4) -> args=(1,2,3,4) -> value=(1,2,3,4)
        self.prim.set_border_color(255, 0, 0, 255)
        self.assertEqual(self.prim.extra[core.KEY_BORDER_COLOR], (255, 0, 0, 255))

    def test_generic_setter_valid_explicit_tuple(self):
        # set_border_color((1, 2, 3, 4)) -> args=((1,2,3,4),) -> value=(1,2,3,4)
        self.prim.set_border_color((10, 20, 30, 40))
        self.assertEqual(self.prim.extra[core.KEY_BORDER_COLOR], (10, 20, 30, 40))

    def test_background_color_mapping(self):
        # set_background_color should map to core.KEY_COLOR
        self.prim.set_background_color(100, 100, 100, 255)
        self.assertEqual(self.prim.extra[core.KEY_COLOR], (100, 100, 100, 255))

    def test_invalid_property_raises(self):
        with self.assertRaises(AttributeError):
            self.prim.set_non_existent_prop(123)

    def test_non_setter_method_missing(self):
        # Ensure normal attribute error for non-setter methods
        with self.assertRaises(AttributeError):
            self.prim.some_other_method()

if __name__ == '__main__':
    unittest.main()
