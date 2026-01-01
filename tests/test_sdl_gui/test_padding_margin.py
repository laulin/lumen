import unittest
from typing import Any, Dict

from sdl_gui.primitives.base import BasePrimitive
from sdl_gui.window.window import Window


class ConcretePrimitive(BasePrimitive):
    def to_data(self) -> Dict[str, Any]:
        return super().to_data()

class TestPaddingMargin(unittest.TestCase):
    def test_normalize_single_int(self):
        p = ConcretePrimitive(0, 0, 10, 10, padding=10)
        self.assertEqual(p.padding, (10, 10, 10, 10))

    def test_normalize_single_str(self):
        p = ConcretePrimitive(0, 0, 10, 10, margin="5px")
        self.assertEqual(p.margin, ("5px", "5px", "5px", "5px"))

    def test_normalize_tuple_2(self):
        p = ConcretePrimitive(0, 0, 10, 10, padding=(10, 20))
        self.assertEqual(p.padding, (10, 20, 10, 20))

    def test_normalize_list_4(self):
        p = ConcretePrimitive(0, 0, 10, 10, margin=[1, 2, 3, 4])
        self.assertEqual(p.margin, (1, 2, 3, 4))

    # test_resolve_px deleted
    # test_resolve_plain_str deleted
    # test_resolve_percent deleted
    pass
