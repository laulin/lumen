import unittest

from sdl_gui import core
from sdl_gui.primitives.base import BasePrimitive


class ConcretePrimitive(BasePrimitive):
    def to_data(self):
        return super().to_data()

class TestBasePrimitiveEvents(unittest.TestCase):
    def test_init_agnostic_events(self):
        """Test initialization with ID and listen_events."""
        p = ConcretePrimitive(x=0, y=0, width=10, height=10,
                            id="my_btn", listen_events=[core.EVENT_CLICK])
        self.assertEqual(p.id, "my_btn")
        self.assertEqual(p.listen_events, [core.EVENT_CLICK])

    def test_to_data_agnostic_events(self):
        """Test data generation with agnostic events."""
        p = ConcretePrimitive(x=0, y=0, width=10, height=10,
                            id="my_btn", listen_events=[core.EVENT_CLICK])
        data = p.to_data()
        self.assertEqual(data[core.KEY_ID], "my_btn")
        self.assertEqual(data[core.KEY_LISTEN_EVENTS], [core.EVENT_CLICK])
