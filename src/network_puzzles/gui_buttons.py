from kivy.app import App
from kivy.uix.button import Button



class ThemedButton(Button):
    pass


class AppButton(ThemedButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()


class MenuButton(AppButton):
    def __init__(self, props, **kwargs):
        super().__init__(**kwargs)
        self.props = props
        self._set_face()
        self._set_callback()

    def _set_callback(self):
        action = self.props.get('action')
        if hasattr(self.app, action):
            self.on_press = getattr(self.app, action)

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


class CommandButton(ThemedButton):
    def __init__(self, callback, command, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.command = command
        # TODO: Parse text from passed command?
        self.text = command
    
    def on_press(self):
        self.callback(self.command)
