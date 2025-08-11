from kivy.uix.label import Label
from kivy.properties import BooleanProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.textinput import TextInput

from .. import session


class TerminalLabel(TextInput):
    def get_max_row(self, text):
        max_row = 0
        max_length = 0
        for i, line in enumerate(text.split("\n")):
            if len(line) > max_length:
                max_row = i
                max_length = len(line)
        return max_row


class ThemedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app


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

    def on_touch_down(self, touch):
        """Add selection on touch down"""
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        if is_selected:
            # Call RecycleView callback with index of selected item.
            rv.on_selection(index)
