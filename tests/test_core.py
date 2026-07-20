import unittest

from network_puzzles import core


class TestValidateJSON(unittest.TestCase):
    def test_multiple_values(self):
        data = {"key": ["value1", "value2"]}
        valid_data = {"key": ["value1", "value2"]}
        core.conform_json_values(data, "key")
        self.assertEqual(data, valid_data)

    def test_no_key(self):
        data = {}
        valid_data = {"key": []}
        core.conform_json_values(data, "key")
        self.assertEqual(data, valid_data)

    def test_no_value(self):
        data = {"key": None}
        valid_data = {"key": []}
        core.conform_json_values(data, "key")
        self.assertEqual(data, valid_data)

    def test_single_value(self):
        data = {"key": "value"}
        valid_data = {"key": ["value"]}
        core.conform_json_values(data, "key")
        self.assertEqual(data, valid_data)
