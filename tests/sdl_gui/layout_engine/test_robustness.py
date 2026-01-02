import unittest
from sdl_gui.layout_engine.definitions import FlexDirection, AlignItems
from sdl_gui.layout_engine.style import FlexStyle
from sdl_gui.layout_engine.node import FlexNode

class TestFlexRobustness(unittest.TestCase):
    def test_main_axis_overflow_distribution(self):
        """Test that overflow reduction is distributed correctly when some children hit zero."""
        root = FlexNode(style=FlexStyle(
            width=100, height=100, direction=FlexDirection.COLUMN
        ))
        child1 = FlexNode(style=FlexStyle(width=100, height=120, shrink=1.0))
        child2 = FlexNode(style=FlexStyle(width=100, height=10, shrink=1.0))
        
        root.add_child(child1)
        root.add_child(child2)
        
        root.calculate_layout(100, 100)
        
        h1 = child1.layout_rect[3]
        h2 = child2.layout_rect[3]
        total = h1 + h2
        
        self.assertLessEqual(total, 100.001, f"Total height {total} exceeds parent height 100")
        self.assertAlmostEqual(h1, 100, delta=0.1)
        self.assertAlmostEqual(h2, 0, delta=0.1)

    def test_cross_axis_overflow_clamping(self):
        """Test that children are clamped to cross axis capacity."""
        root = FlexNode(style=FlexStyle(
            width=100, height=100, direction=FlexDirection.ROW, align_items=AlignItems.CENTER
        ))
        child = FlexNode(style=FlexStyle(width=50, height=150))
        root.add_child(child)
        
        root.calculate_layout(100, 100)
        
        y = child.layout_rect[1]
        h = child.layout_rect[3]
        
        self.assertGreaterEqual(y, 0, f"Child y {y} is negative (starts above parent)")
        self.assertLessEqual(h, 100.001, f"Child height {h} exceeds parent height 100")

    def test_complex_overflow(self):
        """Test multiple items with different shrink factors and some hitting zero."""
        root = FlexNode(style=FlexStyle(width=100, height=100, direction=FlexDirection.COLUMN))
        # Total base height: 50 + 50 + 50 = 150. Overflow = 50.
        # Shrink factors: 1, 1, 3. Total shrink = 5.
        # Unit shrink = 50 / 5 = 10.
        # Child 1: 50 - 10*1 = 40.
        # Child 2: 50 - 10*1 = 40.
        # Child 3: 50 - 10*3 = 20.
        # Total: 40 + 40 + 20 = 100.
        c1 = FlexNode(style=FlexStyle(width=100, height=50, shrink=1.0))
        c2 = FlexNode(style=FlexStyle(width=100, height=50, shrink=1.0))
        c3 = FlexNode(style=FlexStyle(width=100, height=50, shrink=3.0))
        
        root.add_child(c1); root.add_child(c2); root.add_child(c3)
        root.calculate_layout(100, 100)
        
        self.assertAlmostEqual(c1.layout_rect[3], 40, delta=0.1)
        self.assertAlmostEqual(c2.layout_rect[3], 40, delta=0.1)
        self.assertAlmostEqual(c3.layout_rect[3], 20, delta=0.1)

if __name__ == '__main__':
    unittest.main()
