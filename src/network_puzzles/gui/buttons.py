import logging

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.button import Button

from .. import session
from .labels import ToolTip


class ThemedButton(Button):
    LONG_PRESS_THRESHOLD = 0.4
    info = StringProperty()

    def __init__(self, on_release=None, **kwargs):
        super().__init__(**kwargs)
        self.long_press = None
        self.tooltip = ToolTip()
        self._on_release = on_release
        Window.bind(mouse_pos=self.on_mouse_pos)

    @property
    def app(self):
        return session.app

    @property
    def tooltip_anchor(self):
        parent = None
        if isinstance(self, DeviceButton):
            if hasattr(self, "parent") and hasattr(self.parent, "parent"):
                parent = self.parent.parent  # puzzle layout
        elif isinstance(self, MenuButton) and self.text != "+":
            if hasattr(self, "parent") and hasattr(self.parent, "parent"):
                parent = self.parent.parent
        else:
            parent = self.parent  # menu/puzzle layout
        return parent

    @property
    def tooltip_pos(self):
        return self.tooltip.pos

    @tooltip_pos.setter
    def tooltip_pos(self, pos):
        self.tooltip.pos = pos

    @property
    def tooltip_size(self):
        return self.tooltip.size

    @tooltip_size.setter
    def tooltip_size(self, size):
        self.tooltip.size = size

    @property
    def tooltip_text(self):
        return self.tooltip.text

    @tooltip_text.setter
    def tooltip_text(self, text):
        self.tooltip.text = text
        self._update_tooltip_props()

    def on_mouse_pos(self, window, pos):
        if not self.get_root_window():
            return
        # Close tooltip if already open.
        self.cancel_tooltip()
        # Open trigger button's toolip if mouse is over button.
        if self.collide_point(*self.to_widget(*pos)):
            Clock.schedule_once(self.open_tooltip, self.LONG_PRESS_THRESHOLD)

    def on_press(self):
        if self._on_release is None:
            return
        # Schedule long-press callback into the future.
        self.long_press = Clock.schedule_once(
            self._on_long_press, self.LONG_PRESS_THRESHOLD
        )

    def on_release(self):
        self.cancel_tooltip()
        if self._on_release is None:
            return
        # If long-press callback hasn't run, cancel it and run the short-press
        # callback. Here ".is_triggered" means "scheduled but not yet run". It
        # resets to 0 or False after the event is processed.
        if not self.long_press or self.long_press.is_triggered:
            self.long_press.cancel()
            self._on_release()

    def cancel_tooltip(self):
        Clock.unschedule(self.open_tooltip)  # cursor moved, cancel scheduled event
        self.close_tooltip()

    def close_tooltip(self, *args):
        if self.tooltip_anchor:
            self.tooltip_anchor.remove_widget(self.tooltip)

    def open_tooltip(self, *args):
        def no_tooltip(self):
            if not self.info:
                return True
            if not self.parent:
                return True
            if 0 in (self.opacity, self.parent.opacity):
                return True

        # Don't show tooltip in certain cases.
        if no_tooltip(self):
            return
        self.tooltip_text = self.info
        if self.tooltip_anchor is None:
            logging.warning(f"Buttons: {self} has no tooltip_anchor!")
            return
        if self.tooltip not in self.tooltip_anchor.children:
            self.tooltip_anchor.add_widget(self.tooltip)

    def _calc_tooltip_pos(self):
        # Put the tooltip to the right by default.
        sp = dp(3)
        x = self.x + self.width + sp
        y = self.y + self.height - self.tooltip.height
        if self.tooltip_anchor is None:
            logging.warning(f"Buttons: {self} has no tooltip_anchor!")
            return (x, y)
        if x + self.tooltip.width > self.tooltip_anchor.width:
            # Put the tooltip to the left if not enough room to the right.
            x = self.x - self.tooltip.width - sp
        return (x, y)

    def _calc_tooltip_size(self):
        self.tooltip.texture_update()
        return self.tooltip.texture_size

    def _on_long_press(self, *args):
        self.open_tooltip()

    def _update_tooltip_props(self):
        self.tooltip.texture_update()  # depends on text value
        self.tooltip_size = self.tooltip.texture_size
        self.tooltip.text_size = (None, None)
        self.tooltip_pos = self._calc_tooltip_pos()


class AppButton(ThemedButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cb = None
        self.cb_args = list()
        self.cb_kwargs = dict()

    def callback(self):
        if callable(self.cb):
            self.cb(self, *self.cb_args, **self.cb_kwargs)

    def get_pos(self):
        idx = len(self.parent.children) - self.parent.children.index(self) - 1
        button_width = self.size_hint_max_y
        x = self.parent.padding + idx * (button_width + self.parent.spacing)
        y = self.parent.padding
        return (x, y)


class DeviceButton(ThemedButton):
    def on_pos(self, *args):
        # Update drag_rectangle for GuiDevice (parent) widget.
        if hasattr(self, "parent"):
            self.parent.drag_rectangle = [
                *self.parent.drag_rectangle[:3],
                self.parent.get_height(),
            ]


class MenuButton(AppButton):
    def __init__(self, props, **kwargs):
        super().__init__(**kwargs)
        self.props = props
        self.info = self._set_info()
        self._set_size_hint()
        self._set_face()
        self._set_callback()

    def _set_callback(self):
        self.cb = self.props.get("cb")
        self.cb_args = self.props.get("cb_args", list())
        self.cb_kwargs = self.props.get("cb_kwargs", dict())

    def _set_face(self):
        text = self.props.get("text")
        if text:
            self.text = text
            self.background_normal = ""
        img = self.props.get("img")
        if img:
            self.text = ""
            self.background_color[3] = 1  # make it opaque so the image is visible
            self.background_normal = str(self.app.IMAGES / img)

    def _set_info(self):
        info = ""  # must be type "str"
        puzzle_info = self.props.get("info")
        puzzle_img = self.props.get("img")
        if puzzle_info:
            info = puzzle_info
        elif puzzle_img:
            info = puzzle_img.lower().rstrip(".png")
        return info

    def _set_size_hint(self):
        if self.props.get("orientation") == "horizontal":
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

    def on_release(self):
        self.cb(self.command)
        # Find parent Popup and dismiss it.
        popup = self.parent
        while not hasattr(popup, "dismiss"):
            popup = popup.parent
        popup.dismiss()
