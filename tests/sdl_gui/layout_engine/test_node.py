import unittest
from sdl_gui.layout_engine.definitions import FlexDirection, JustifyContent, AlignItems
from sdl_gui.layout_engine.style import FlexStyle
from sdl_gui.layout_engine.node import FlexNode

class TestFlexNode(unittest.TestCase):
    def test_simple_layout(self):
        """Test basic layout calculation with fixed sizes."""
        root = FlexNode(style=FlexStyle(
            width=100,
            height=100,
            direction=FlexDirection.ROW
        ))
        child1 = FlexNode(style=FlexStyle(width=50, height=20))
        child2 = FlexNode(style=FlexStyle(width=50, height=20))
        
        root.add_child(child1)
        root.add_child(child2)
        
        root.calculate_layout(100, 100)
        
        self.assertEqual(root.layout_rect, (0, 0, 100, 100))
        self.assertEqual(child1.layout_rect, (0, 0, 50, 20))
        self.assertEqual(child2.layout_rect, (50, 0, 50, 20))

    def test_flex_grow(self):
        """Test flex-grow property."""
        root = FlexNode(style=FlexStyle(
            width=100,
            height=100,
            direction=FlexDirection.ROW
        ))
        # Child 1 fixed width 20, Child 2 grow=1, Child 3 grow=1
        child1 = FlexNode(style=FlexStyle(width=20, height=20))
        child2 = FlexNode(style=FlexStyle(grow=1, height=20, width=0))
        child3 = FlexNode(style=FlexStyle(grow=1, height=20, width=0))
        
        root.add_child(child1)
        root.add_child(child2)
        root.add_child(child3)
        
        root.calculate_layout(100, 100)
        
        # Available space = 100 - 20 = 80. Split 80 / 2 = 40 each.
        self.assertEqual(child1.layout_rect, (0, 0, 20, 20)) # x=0, w=20
        self.assertEqual(child2.layout_rect, (20, 0, 40, 20)) # x=20, w=40
        self.assertEqual(child3.layout_rect, (60, 0, 40, 20)) # x=60, w=40

    def test_justify_content_center(self):
        """Test justify-content: center."""
        root = FlexNode(style=FlexStyle(
            width=100,
            height=100,
            direction=FlexDirection.ROW,
            justify_content=JustifyContent.CENTER
        ))
        child = FlexNode(style=FlexStyle(width=50, height=50))
        root.add_child(child)
        
        root.calculate_layout(100, 100)
        
        # Space free = 50. Start = 50/2 = 25.
        self.assertEqual(child.layout_rect, (25, 0, 50, 50))

    def test_align_items_center(self):
        """Test align-items: center."""
        root = FlexNode(style=FlexStyle(
            width=100,
            height=100,
            direction=FlexDirection.ROW,
            align_items=AlignItems.CENTER
        ))
        child = FlexNode(style=FlexStyle(width=50, height=50))
        root.add_child(child)
        
        root.calculate_layout(100, 100)
        
        # Cross axis (height): (100 - 50) / 2 = 25
        self.assertEqual(child.layout_rect, (0, 25, 50, 50))
    
    def test_column_layout(self):
        """Test column layout."""
        root = FlexNode(style=FlexStyle(
            width=100,
            height=100,
            direction=FlexDirection.COLUMN
        ))
        child1 = FlexNode(style=FlexStyle(width=100, height=20))
        child2 = FlexNode(style=FlexStyle(width=100, height=30))
        
        root.add_child(child1)
        root.add_child(child2)
        
        root.calculate_layout(100, 100)
        
        self.assertEqual(child1.layout_rect, (0, 0, 100, 20))
        self.assertEqual(child2.layout_rect, (0, 20, 100, 30))

if __name__ == '__main__':
    unittest.main()
