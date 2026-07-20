from copy import deepcopy

from . import session
from .core import ItemBase


class Shape(ItemBase):
    EMPTY_SHAPE_JSON = {
        "name": "ShapeName",
        "what": "rectangle",  # Could be rectangle or circle, but puzzles only use rectangle.
        "where": "100,100,200,200",  # Two x,y coordinates.
        "fillcolor": "Gray",  # A color: Blue, Gray, Green, LightGreen, SaddleBrown
        "linecolor": "Gray",  # A color: Blue, Gray, Green, LightGreen, SaddleBrown
    }

    def __init__(self, json_data=None):
        if json_data is None:
            # deepcopy keeps class attribute from being changed.
            json_data = deepcopy(self.EMPTY_SHAPE_JSON)
            # Seconds since epoc. Failsafe that will kill the packet if too much time has passed
        super().__init__(json_data)
        self.session = session

    @property
    def name(self):
        return self.json.get("name")

    @name.setter
    def name(self, value):
        self.json["name"] = value

    @property
    def what(self):
        return self.json.get("what")

    @what.setter
    def what(self, value):
        self.json["what"] = value

    @property
    def fillcolor(self):
        return self.json.get("fillcolor")

    @fillcolor.setter
    def fillcolor(self, value):
        self.json["fillcolor"] = value

    @property
    def linecolor(self):
        return self.json.get("linecolor")

    @linecolor.setter
    def linecolor(self, value):
        self.json["linecolor"] = value

    @property
    def where(self):
        # This should return x1, y1, x2, y2
        return self.json.get("where").split(",")

    @where.setter
    def where(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            self.json["where"] = ",".join(value)
        else:
            if isinstance(value, str):
                self.json["where"] = value
