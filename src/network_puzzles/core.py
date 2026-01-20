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
