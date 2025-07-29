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
        size = (1280.0, 720.0)
        self.assertEqual(
            self.base.pos_to_location([25.0, 25.0], size),
            [str(0.0), str(float(self.base.LOCATION_MAX_Y))],
        )
        # Test bottom-left pos, outside of padding
        self.assertEqual(
            self.base.pos_to_location([0.0, 0.0], size),
            [str(0.0), str(float(self.base.LOCATION_MAX_Y))],
        )
        # Test bottom-center pos.
        # Test bottom-right pos.
        # Test center-left pos.
        self.assertEqual(
            self.base.pos_to_location([0, size[1] / 2], size),
            [str(0.0), str(float(self.base.LOCATION_MAX_Y / 2))],
        )
        # Test center-center pos. 1222x645.3
        self.assertEqual(
            self.base.pos_to_location([size[0] / 2, size[1] / 2], size),
            [
                str(float(self.base.LOCATION_MAX_X / 2)),
                str(float(self.base.LOCATION_MAX_Y / 2)),
            ],
        )
        # Test center-right pos.
        # Test top-left pos.
        self.assertEqual(
            self.base.pos_to_location([0.0, 900.0], size),
            [str(0.0), str(0.0)],
        )
        # Test top-center pos.
        # Test top-right pos.

    def test_pos_to_rel_pos(self):
        self.assertEqual(self.base.pos_to_rel_pos([0, 0]), [0, 0])
        self.assertEqual(
            self.base.pos_to_rel_pos([self.base.PADDED_MAX_X, self.base.PADDED_MAX_Y]),
            [1, 1],
        )
