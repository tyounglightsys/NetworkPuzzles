from kivy.properties import BooleanProperty
from kivy.uix.label import Label
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

    def on_touch_up(self, touch):
        # REF: https://kivy.org/doc/master/guide/inputs.html#grabbing-touch-events
        # Open popup on right-click within the Terminal area (only works on
        # desktop devices).
        if touch.button == "right" and touch.grab_current is self:
            touch.ungrab(self)
            CommandPopup().open()
            return True


class ThemedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app


class CheckBoxLabel(ThemedLabel):
    pass


class DeviceLabel(ThemedLabel):
    pass


class InfoLabel(ThemedLabel):
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
            (touch.button == "left" or touch.button is None)
            and self.collide_point(*touch.pos)
            and self.selectable
        ):
            self.parent.select_with_touch(self.index, touch)
            return True

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        if is_selected:
            # Call RecycleView callback with index of selected item.
            rv.on_selection(index)
