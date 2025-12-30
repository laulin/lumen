import unittest
from sdl_gui.primitives.base import BasePrimitive
from typing import Dict, Any

class ConcretePrimitive(BasePrimitive):
    def to_data(self) -> Dict[str, Any]:
        data = super().to_data()
        data["type"] = "concrete"
        return data

class TestBasePrimitive(unittest.TestCase):
    def test_init_defaults(self):
        """Test initialization with default values."""
        p = ConcretePrimitive(x=0, y=0, width=100, height=100)
        self.assertEqual(p.padding, (0, 0, 0, 0))
        self.assertEqual(p.margin, (0, 0, 0, 0))

    def test_init_custom(self):
        """Test initialization with custom padding/margin."""
        p = ConcretePrimitive(x=0, y=0, width=100, height=100, 
                            padding=(1, 2, 3, 4), margin=(5, 6, 7, 8))
        self.assertEqual(p.padding, (1, 2, 3, 4))
        self.assertEqual(p.margin, (5, 6, 7, 8))

    def test_to_data(self):
        """Test base data generation."""
        p = ConcretePrimitive(x=10, y=20, width=30, height=40,
                            padding=(1, 1, 1, 1), margin=(2, 2, 2, 2))
        data = p.to_data()
        self.assertEqual(data["rect"], [10, 20, 30, 40])
        self.assertEqual(data["padding"], (1, 1, 1, 1))
        self.assertEqual(data["margin"], (2, 2, 2, 2))
