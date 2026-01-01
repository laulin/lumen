import unittest

from sdl_gui.primitives.base import BasePrimitive


class MockPrimitive(BasePrimitive):
    def to_data(self):
        return super().to_data()

class TestColor(unittest.TestCase):
    def test_color_normalization_setter(self):
        p = MockPrimitive(0,0,10,10)

        # Test 3-tuple -> 4-tuple normalization
        p.set_color(100, 150, 200)
        self.assertEqual(p.extra['color'], (100, 150, 200, 255))

        # Test 4-tuple preservation
        p.set_color(10, 20, 30, 40)
        self.assertEqual(p.extra['color'], (10, 20, 30, 40))

        # Test list -> tuple
        p.set_color([50, 60, 70])
        self.assertEqual(p.extra['color'], (50, 60, 70, 255))

    def test_background_color_alias(self):
        p = MockPrimitive(0,0,10,10)
        p.set_background_color(255, 0, 0)
        self.assertEqual(p.extra['color'], (255, 0, 0, 255))

if __name__ == '__main__':
    unittest.main()
