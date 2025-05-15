from kivy.app import App
from kivy.core.window import Window


class NetworkPuzzlesApp(App):
    DARK_COLOR = (0.1, 0.1, 0.1, 1)
    LIGHT_COLOR = (0.8, 0.8, 0.8, 1)
    LIGHTER_COLOR = (0.95, 0.95, 0.95, 1)
    LIGHTEST_COLOR = (0.98, 0.98, 0.98, 1)
    Window.clearcolor = LIGHTER_COLOR
    Window.size = (1600, 720)  # 20:9 aspect ratio

    def on_help(self):
        print('help clicked')

    def on_menu(self):
        print('menu clicked')