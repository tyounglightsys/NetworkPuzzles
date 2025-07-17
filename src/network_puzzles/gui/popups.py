import logging
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.uix.popup import Popup

from .. import session


class AppPopup(Popup):
    def __init__(self, **kwargs):
        # TODO: This popup automatically generates a GridLayout with 3 child
        # widgets: BoxLayout, Widget, Label. Better to set the content
        # explicitly when the popup is instantiated elsewhere.
        self.app = session.app
        super().__init__(**kwargs)

    def _update_sep_color(self):
        # Set separator color according to theme.
        w = self.children[0].children[1]
        with w.canvas:
            Color(rgba=self.app.theme.detail)
            Rectangle(pos=w.pos, size=w.size)

    def on_open(self):
        self._update_sep_color()


class CommandsPopup(AppPopup):
    pass


class ExceptionPopup(AppPopup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.ids.exception.text = message

    def on_dismiss(self):
        # Don't allow the app to continue running.
        self.app.stop()


class LinkPopup(AppPopup):
    def __init__(self, widget, **kwargs):
        super().__init__(**kwargs)
        self.link = widget
        self.title = self.link.base.json.get("hostname", "<hostname>")

    def delete(self):
        self.app.remove_item(self.link)
        self.dismiss()

    def edit(self):
        self.link.edit()
        self.dismiss()


class PingHostPopup(AppPopup):
    def on_cancel(self):
        self.dismiss()

    def on_okay(self, text):
        self.app.ui.parse(f"ping {self.title.split()[-1]} {text}")
        self.dismiss()


class PuzzleChooserPopup(AppPopup):
    def on_cancel(self):
        self.dismiss()

    def on_dismiss(self):
        self.app.selected_puzzle = None

    def on_load(self):
        self.app.ui.load_puzzle(self.app.selected_puzzle)
        self.app.setup_puzzle(self.app.ui.puzzle.json)
        self.dismiss()


class EditDevicePopup(AppPopup):
    def __init__(self, device, **kwargs):
        self.device = device
        super().__init__(**kwargs)

    def get_editable_nic_names(self):
        return "\n".join(
            [n.name for n in self.device.nics if not n.name.startswith("lo")]
        )

    def on_gateway(self):
        raise NotImplementedError

    def on_routes(self):
        raise NotImplementedError

    def on_vlans(self):
        raise NotImplementedError

    def on_nics_edit(self):
        raise NotImplementedError

    def on_ips_add(self):
        raise NotImplementedError

    def on_ips_remove(self):
        raise NotImplementedError

    def on_ips_edit(self):
        raise NotImplementedError

    def on_okay(self):
        logging.debug("GUI: TODO: Apply config updates on exit.")
        raise NotImplementedError
