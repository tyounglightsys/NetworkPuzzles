import unittest


class TestCoordConversions(unittest.TestCase):
    def setUp(self):
        # Import GUI modules here to avoid extra log/console output.
        from network_puzzles.gui import base

        self.base = base

    def test_location_to_position(self):
        x = 0
        y = 0
        self.assertEqual(
            self.base.location_to_pos(f"{x},{y}"),
            [self.base.PADDING, self.base.PADDING + self.base.LOCATION_MAX_Y],
        )
        x = 100
        y = 100
        self.assertEqual(
            self.base.location_to_pos(f"{x},{y}"),
            [self.base.PADDING + x, self.base.PADDING + self.base.LOCATION_MAX_Y - y],
        )

    def test_pos_to_location(self):
        # Test bottom-left pos, inside of padding.
        self.assertEqual(
            self.base.pos_to_location([25, 25]), [str(0), str(self.base.LOCATION_MAX_Y)]
        )
        # Test bottom-left pos, outside of padding
        self.assertEqual(
            self.base.pos_to_location([0, 0]), [str(0), str(self.base.LOCATION_MAX_Y)]
        )

    def test_pos_to_rel_pos(self):
        self.assertEqual(self.base.pos_to_rel_pos([0, 0]), [0, 0])
        self.assertEqual(
            self.base.pos_to_rel_pos([self.base.PADDED_MAX_X, self.base.PADDED_MAX_Y]),
            [1, 1],
        )
