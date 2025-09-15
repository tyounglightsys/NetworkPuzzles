import logging
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.properties import ListProperty
from kivy.uix.widget import Widget

from .. import link
from .. import session
from .base import hide_widget
from .popups import AppPopup


class Link(Widget):
    end = ListProperty(None)
    start = ListProperty(None)

    def __init__(self, init_data=None, **kwargs):
        self.app = session.app
        super().__init__(**kwargs)
        self.base = link.Link(init_data)

        self._set_points()
        self._set_size_and_pos()

        self.background_normal = ""
        self._draw_line()

    @property
    def hostname(self):
        if hasattr(self, "base"):
            return self.base.hostname
        else:
            return None

    @property
    def uniqueidentifier(self):
        if hasattr(self, "base"):
            return self.base.uniqueidentifier
        else:
            return None

    def _draw_line(self):
        self.canvas.clear()
        with self.canvas:
            Color(rgba=self.app.theme.fg1)
            Line(points=(*self.start, *self.end), width=2)

    def edit(self):
        # TODO: Add Edit Link Popup.
        raise NotImplementedError

    def get_progress_pos(self, progress):
        dx = progress * (self.end[0] - self.start[0]) / 100
        dy = progress * (self.end[1] - self.start[1]) / 100
        return (self.start[0] + dx, self.start[1] + dy)

    def hide(self, do_hide=True):
        hide_widget(self, do_hide)

    def move_connection(self, dev):
        # Update link properties.
        if self.hostname.startswith(dev.hostname):
            self._set_startpoint(dev)
        elif self.hostname.endswith(dev.hostname):
            self._set_endpoint(dev)
        self._set_size_and_pos()
        # Redraw the link line.
        self._draw_line()

    def on_touch_up(self, touch):
        if touch.button == "left" and self.collide_point(*touch.pos):
            LinkPopup(self).open()
            return True

    def set_end_nic(self):
        # TODO: Set hostname once DstNic is set as:
        # "SrcNicHostname_link_DstNicHostname"
        raise NotImplementedError

    def set_link_type(self):
        # Set one of: 'broken', 'normal', 'wireless'
        raise NotImplementedError

    def set_start_nic(self):
        raise NotImplementedError

    def _set_uid(self):
        raise NotImplementedError

    def _set_endpoint(self, end_dev=None):
        if end_dev is None:
            end_dev = self.app.get_widget_by_hostname(
                self.base.json.get("DstNic").get("hostname")
            )
        self.end = end_dev.button.center

    def _set_startpoint(self, start_dev=None):
        if start_dev is None:
            start_dev = self.app.get_widget_by_hostname(
                self.base.json.get("SrcNic").get("hostname")
            )
        self.start = start_dev.button.center

    def _set_points(self):
        self._set_startpoint()
        self._set_endpoint()

    def _set_size_and_pos(self):
        # Set pos.
        self.x = min([self.start[0], self.end[0]])
        self.y = min([self.start[1], self.end[1]])
        # Set size.
        self.size_hint = (None, None)
        w = self.start[0] - self.end[0]
        if w < 0:
            w = -1 * w
        self.width = w
        h = self.start[1] - self.end[1]
        if h < 0:
            h = -1 * h
        self.height = h


class LinkPopup(AppPopup):
    def __init__(self, widget, **kwargs):
        super().__init__(**kwargs)
        self.link = widget
        self.title = self.link.hostname

    def delete(self):
        self.app.ui.parse(f"delete {self.link.hostname}")
        self.app.remove_item(self.link)
        self.dismiss()

    def edit(self):
        self.link.edit()
        self.dismiss()
