import unittest
from sdl_gui.primitives.base import BasePrimitive
from sdl_gui import core

class ConcretePrimitive(BasePrimitive):
    def to_data(self):
        return super().to_data()

class TestBasePrimitiveEvents(unittest.TestCase):
    def test_init_events(self):
        """Test initialization with events."""
        events = {core.EVENT_CLICK: lambda: None}
        p = ConcretePrimitive(x=0, y=0, width=10, height=10, events=events)
        self.assertEqual(p.events, events)

    def test_to_data_events(self):
        """Test events in data generation."""
        events = {core.EVENT_CLICK: lambda: None}
        p = ConcretePrimitive(x=0, y=0, width=10, height=10, events=events)
        data = p.to_data()
        self.assertEqual(data[core.KEY_EVENTS], events)
