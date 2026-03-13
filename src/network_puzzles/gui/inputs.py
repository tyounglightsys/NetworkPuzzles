from kivy.clock import Clock
from kivy.uix.textinput import TextInput


class ValueInput(TextInput):
    def schedule_select_all(self):
        # NOTE: The delay needs to be > 0 sec (next frame), otherwise
        # the select_all action is overridden by default deselect_all.
        delay = 0.1
        Clock.schedule_once(lambda dt: self.select_all(), delay)
