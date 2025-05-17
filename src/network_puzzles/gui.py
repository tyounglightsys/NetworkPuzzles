import traceback
from kivy.app import App
from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.core.window import Window
from kivy.uix.popup import Popup


class NetworkPuzzlesApp(App):
    DARK_COLOR = (0.1, 0.1, 0.1, 1)
    LIGHT_COLOR = (0.8, 0.8, 0.8, 1)
    LIGHTER_COLOR = (0.95, 0.95, 0.95, 1)
    LIGHTEST_COLOR = (0.98, 0.98, 0.98, 1)
    Window.clearcolor = LIGHTER_COLOR
    Window.size = (1600, 720)  # 20:9 aspect ratio

    def __init__(self, ui, **kwargs):
        super().__init__(**kwargs)
        ExceptionManager.add_handler(AppExceptionHandler())
        self.ui = ui
        self.ct = 1

    def add_terminal_line(self, line):
        if not line.endswith('\n'):
            line += '\n'
        self.root.ids.terminal.text += f"{line}"

    def on_help(self):
        print('help clicked')

    def on_menu(self):
        print('menu clicked')

    def _test(self, *args, **kwargs):
        raise NotImplementedError


class AppExceptionHandler(ExceptionHandler):
    def handle_exception(self, exception):
        print(dir(exception), str(exception.__traceback__.__dir__()))
        ExceptionPopup(message=traceback.format_exc()).open()
        return ExceptionManager.PASS


class ExceptionPopup(Popup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.ids.message.text = message
    
    def on_dismiss(self):
        # Don't allow the app to continue running.
        self.app.stop()