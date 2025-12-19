from kivy.properties import BooleanProperty
from kivy.uix.label import Label
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from .. import session


class ThemedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def app(self):
        return session.app


class CheckBoxLabel(ThemedLabel):
    pass


class DeviceLabel(ThemedLabel):
    pass


class InfoLabel(ThemedLabel):
    pass


class ToolTip(ThemedLabel):
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
