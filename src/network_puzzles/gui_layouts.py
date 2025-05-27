from kivy.app import App
from kivy.metrics import dp
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

from .gui_buttons import MenuButton

class ThemedBoxLayout(BoxLayout):
    pass


class AppMenu(ThemedBoxLayout):
    def __init__(self, anchor_pos=None, choices=list(), orientation='horizontal', **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.size_hint = (None, None)
        self.orientation = orientation
        if self.orientation == 'horizontal':
            self.padding[1] = 0
            self.padding[3] = 0
        else:
            self.padding[0] = 0
            self.padding[2] = 0
        self.anchor_pos = anchor_pos  # parent_button.pos as (x, y)
        print(f"{self.anchor_pos=}")
        self.choices = choices

    def open(self):
        for c in self.choices:
            self.add_widget(MenuButton(c))
        self._set_size()
        self._set_pos()

    def close(self):
        self.clear_widgets()

    def _set_pos(self):
        if self.orientation == 'horizontal':
            # NOTE: The tray's pos is immediately adjacent to the anchor button.
            x = self.anchor_pos[0] + self.height
            y = self.anchor_pos[1]
        else:
            # NOTE: The tray's pos is offset down from the anchor button by the
            # tray's height.
            x = self.anchor_pos[0]
            y = self.anchor_pos[1] - self.height
        self.pos = (x, y)
    
    def _set_size(self):
        length = len(self.children)
        breadth = dp(self.app.BUTTON_MAX_H + 10)  # 10px more for padding
        # breadth = dp(self.app.BUTTON_MAX_H)
        if self.orientation == 'horizontal':
            self.width = length * breadth
            self.height = breadth
        else:
            self.width = breadth
            self.height = length * breadth
        print(f"{self.orientation=}; {self.size=}; {self.padding=}; {self.spacing=}")


class SelectableRecycleBoxLayout(
    FocusBehavior,
    LayoutSelectionBehavior,
    RecycleBoxLayout
):
    ''' Adds selection and focus behaviour to the view. '''
    pass
