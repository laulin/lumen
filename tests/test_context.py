import unittest

from sdl_gui import context
from sdl_gui.layers.layer import Layer
from sdl_gui.layouts.hbox import HBox
from sdl_gui.primitives.base import BasePrimitive
from sdl_gui.primitives.container import Container
from sdl_gui.window.window import Window


class MockPrimitive(BasePrimitive):
    def to_data(self):
        return super().to_data()

class MockContainer(Container):
    def to_data(self):
        return super().to_data()

class TestContext(unittest.TestCase):
    def tearDown(self):
        # Clear context stack
        while context.pop_parent():
            pass

    def test_context_stack_basic(self):
        self.assertIsNone(context.get_current_parent())

        c = MockContainer(0,0,10,10)
        with c:
            self.assertEqual(context.get_current_parent(), c)

        self.assertIsNone(context.get_current_parent())

    def test_nested_context(self):
        c1 = MockContainer(0,0,10,10)
        c2 = MockContainer(0,0,10,10)

        with c1:
            self.assertEqual(context.get_current_parent(), c1)
            with c2:
                self.assertEqual(context.get_current_parent(), c2)
            self.assertEqual(context.get_current_parent(), c1)

    def test_implicit_parenting(self):
        c = MockContainer(0,0,100,100)
        c.children = [] # Ensure it has children list

        with c:
            p = MockPrimitive(0,0,10,10)

        self.assertIn(p, c.children)

    def test_hbox_implicit(self):
        hbox = HBox(0,0,100,100)
        with hbox:
            p = MockPrimitive(0,0,10,10)

        self.assertIn(p, hbox.children)

    def test_window_implicit(self):
        # Window needs a display or size
        w = Window("Test", 800, 600)

        with w:
            l = Layer(0,0,"100%","100%")

        # Check if window captured the layer
        # Depends on our implementation of add_child in Window
        self.assertTrue(hasattr(w, 'root_children'))
        self.assertIn(l, w.root_children)

if __name__ == '__main__':
    unittest.main()
