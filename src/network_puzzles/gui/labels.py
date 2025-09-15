import logging
from kivy.uix.label import Label
from kivy.properties import BooleanProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.textinput import TextInput

from .. import session
from .popups import CommandPopup


class TerminalLabel(TextInput):
    def get_max_row(self, text):
        max_row = 0
        max_length = 0
        for i, line in enumerate(text.split("\n")):
            if len(line) > max_length:
                max_row = i
                max_length = len(line)
        return max_row

    # def on_touch_up(self, touch):
    #     # Open popup on right-click within the Terminal area.
    #     if touch.button == "right" and self.collide_point(*touch.pos):
    #         print(f"right-click registered in terminal area: {touch}")
    #         CommandPopup().open()
    #         return True
    #     # else:
    #     #     return super().on_touch_up(touch)


class ThemedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app


class DeviceLabel(ThemedLabel):
    pass


class ToolTip(ThemedLabel):
    # Added here import access.
    pass


class SelectableLabel(RecycleDataViewBehavior, ThemedLabel):
    """Add selection support to the Label"""

    index = None
    selectable = BooleanProperty(True)
    selected = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)

    def on_touch_up(self, touch):
        """Add selection on touch up"""
        if (
            touch.button == "left"
            and self.collide_point(*touch.pos)
            and self.selectable
        ):
            for k, v in touch.__dict__.items():
                logging.debug(f"{k}={v}")
            # return self.parent.select_with_touch(self.index, touch)
            self.parent.select_with_touch(self.index, touch)
            return True
        # elif super(SelectableLabel, self).on_touch_up(touch):
        #     return True

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        if is_selected:
            # Call RecycleView callback with index of selected item.
            rv.on_selection(index)
