from kivy.app import App
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

from .gui_buttons import MenuButton

class ThemedBoxLayout(BoxLayout):
    pass


class AppMenu(ThemedBoxLayout):
    def __init__(self, choices=list(), base_button=None, direction='horizontal', **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.size_hint: (None, None)
        self.orientation = direction
        if direction == 'horizontal':
            self.padding[1] = 0
            self.padding[3] = 0
        elif direction == 'vertical':
            self.padding[0] = 0
            self.padding[2] = 0
        self.base_button = base_button
        self.direction = direction
        self.choices = choices

    def open(self):
        for c in self.choices:
            self.add_widget(MenuButton(c))
        self._set_size()
        self._set_pos()

    def close(self):
        self.clear_widgets()

    def _set_pos(self):
        if self.direction == 'horizontal':
            x = self.base_button.x + self.width
            y = self.base_button.y
        else:
            x = self.base_button.x
            y = self.base_button.y - self.height
        self.pos = (x, y)
    
    def _set_size(self):
        length = len(self.children)
        if self.direction == 'horizontal':
            self.width = length*58
            self.height = 58
        else:
            self.width = 58
            self.height = length*58


class InsertMenu(AppMenu):
    def __init__(self, **kwargs):
        super().__init__(direction='vertical', **kwargs)
        self.link_item = MenuButton({'img': 'link.png', 'action': 'on_new_link'})
        self.infra_item = MenuButton({'img': 'Switch.png', 'action': 'on_new_infra_device'})
        self.user_item = MenuButton({'img': 'PC.png', 'action': 'on_new_user_device'})

    def open(self):
        self.add_widget(self.link_item)
        self.add_widget(self.infra_item)
        self.add_widget(self.user_item)
        self._set_size()
        self._set_pos()

class SelectableRecycleBoxLayout(
    FocusBehavior,
    LayoutSelectionBehavior,
    RecycleBoxLayout
):
    ''' Adds selection and focus behaviour to the view. '''
    pass
