class ItemBase:
    """Base class for all puzzle items that provides access to item's JSON data."""

    def __init__(self, json_data=None):
        if json_data is not None:
            if not isinstance(json_data, dict):
                raise ValueError(
                    f"{self.__class__} requires JSON data, not '{type(json_data)}'."
                )
            self.json = json_data
        else:
            self.json = {}


def get_coordinate_distance(sx, sy, dx, dy):
    # The ** is the exponent.  **2 is squared, **.5 is the square-root
    return (((sx - dx) ** 2) + ((sy - dy) ** 2)) ** 0.5


def get_puzzle_distance(sx, sy, dx, dy, scale=5):
    # The puzzle layout uses a 5/5 grid.
    return get_coordinate_distance(sx, sy, dx, dy) / scale


def conform_json_values(json_data, key):
    """Ensures proper data format for JSON keys with list values."""
    current_values = json_data.get(key)
    if isinstance(current_values, list):
        # Data is properly conformed.
        return
    elif current_values is None:
        # Make values an empy list.
        json_data[key] = []
    else:
        # Make values a single-item list.
        json_data[key] = [current_values]
