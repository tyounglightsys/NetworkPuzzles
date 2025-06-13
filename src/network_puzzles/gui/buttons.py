from kivy.clock import Clock
from kivy.uix.button import Button

from .. import session


class ThemedButton(Button):
    pass


class AppButton(ThemedButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app
        self.cb = None
        self.cb_args = list()
        self.cb_kwargs = dict()

    def callback(self):
        if callable(self.cb):
            self.cb(self, *self.cb_args, **self.cb_kwargs)


class DeviceButton(ThemedButton):
    LONG_PRESS_THRESHOLD = 0.4

    def __init__(self, on_press, on_long_press, **kwargs):
        super().__init__(**kwargs)
        self.long_press = None
        self._on_press = on_press
        self._on_long_press = on_long_press
    
    def on_press(self):
        # Schedule long-press callback into the future.
        self.long_press = Clock.schedule_once(self._on_long_press, self.LONG_PRESS_THRESHOLD)

    def on_release(self):
        # If long-press callback hasn't run, cancel it and run the short-press
        # callback. Here ".is_triggered" means "scheduled but not yet run". It
        # resets to 0 or False after the event is processed.
        if not self.long_press or self.long_press.is_triggered:
            self.long_press.cancel()
            self._on_press()

class MenuButton(AppButton):
    def __init__(self, props, **kwargs):
        super().__init__(**kwargs)
        self.props = props
        self._set_size_hint()
        self._set_face()
        self._set_callback()

    def _set_callback(self):
        self.cb = self.props.get('cb')
        self.cb_args = self.props.get('cb_args', list())
        self.cb_kwargs = self.props.get('cb_kwargs', dict())

    def _set_face(self):
        text = self.props.get('text')
        if text:
            self.text = text
            self.background_normal = ''
        img = self.props.get('img')
        if img:
            self.text = ''
            self.background_color[3] = 1  # make it opaque so the image is visible
            self.background_normal = str(self.app.IMAGES / img)

    def _set_size_hint(self):
        if self.props.get('orientation') == 'horizontal':
            self.size_hint = (1, None)  # to set explicit height
            self.width = self.app.BUTTON_MAX_H
            self.height = self.width


class CommandButton(ThemedButton):
    def __init__(self, callback, command, **kwargs):
        super().__init__(**kwargs)
        self.cb = callback
        self.command = command
        # TODO: Parse text from passed command?
        self.text = command
    
    def on_press(self):
        self.cb(self.command)
        # Find parent Popup and dismiss it.
        popup = self.parent
        while not hasattr(popup, 'dismiss'):
            popup = popup.parent
        popup.dismiss()
