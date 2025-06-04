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
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback


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
