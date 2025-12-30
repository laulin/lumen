import unittest
from sdl_gui.primitives.base import BasePrimitive
from sdl_gui.window.window import Window
from typing import Dict, Any

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

    def test_resolve_px(self):
        win = Window("Test", 100, 100)
        self.assertEqual(win._resolve_val("10px", 200), 10)
        self.assertEqual(win._resolve_val("20px", 200), 20)
        
    def test_resolve_plain_str(self):
        win = Window("Test", 100, 100)
        self.assertEqual(win._resolve_val("30", 200), 30)
        
    def test_resolve_percent(self):
        win = Window("Test", 100, 100)
        self.assertEqual(win._resolve_val("50%", 200), 100)
