import unittest


class TestCoordConversions(unittest.TestCase):
    def setUp(self):
        # Import GUI modules here to avoid extra log/console output.
        from network_puzzles.gui import base

        self.base = base
        self.size = (1280.0, 720.0)

    def test_location_to_position(self):
        x = 0
        y = 0
        self.assertEqual(
            self.base.location_to_pos((x, y), self.size),
            (float(self.base.PADDING), float(self.size[1] - self.base.PADDING)),
        )
        x = self.base.LOCATION_MAX_X
        y = self.base.LOCATION_MAX_Y
        self.assertEqual(
            self.base.location_to_pos((x, y), self.size),
            (float(self.size[0] - self.base.PADDING), float(self.base.PADDING)),
        )

    def test_pos_to_location(self):
        # Test bottom-left pos, inside of padding.
        self.assertEqual(
            self.base.pos_to_location(
                [self.base.PADDING, self.base.PADDING], self.size
            ),
            (0, self.base.LOCATION_MAX_Y),
        )
        # Test bottom-left pos, outside of padding
        self.assertEqual(
            self.base.pos_to_location([0.0, 0.0], self.size),
            (0, self.base.LOCATION_MAX_Y),
        )
        # Test bottom-center pos.
        # Test bottom-right pos, outside of padding.
        self.assertEqual(
            self.base.pos_to_location([self.size[0], 0.0], self.size),
            (self.base.LOCATION_MAX_X, self.base.LOCATION_MAX_Y),
        )
        # Test bottom-right pos, inside of padding.
        self.assertEqual(
            self.base.pos_to_location(
                [self.size[0] - self.base.PADDING, self.base.PADDING], self.size
            ),
            (self.base.LOCATION_MAX_X, self.base.LOCATION_MAX_Y),
        )
        # Test center-left pos.
        self.assertEqual(
            self.base.pos_to_location([0, self.size[1] / 2], self.size),
            (0, round(self.base.LOCATION_MAX_Y / 2)),
        )
        # Test center-center pos. 1222x645.3
        self.assertEqual(
            self.base.pos_to_location([self.size[0] / 2, self.size[1] / 2], self.size),
            (
                round(self.base.LOCATION_MAX_X / 2),
                round(self.base.LOCATION_MAX_Y / 2),
            ),
        )
        # Test center-right pos.
        # Test top-left pos.
        self.assertEqual(
            self.base.pos_to_location([0.0, self.base.LOCATION_MAX_Y], self.size),
            (0, 0),
        )
        # Test top-center pos.
        # Test top-right pos.

    def test_pos_to_rel_pos(self):
        self.assertEqual(self.base.pos_to_rel_pos([0, 0], self.size), (0, 0))
        self.assertEqual(
            self.base.pos_to_rel_pos([self.size[0], self.size[1]], self.size),
            (1, 1),
        )
