import logging

from kivy.uix.dropdown import DropDown

from network_puzzles import session
from network_puzzles.gui.popups import AppRestartPopup
from network_puzzles.vars import USER_DATA_DIR

langfile = USER_DATA_DIR / "lang.txt"


class LangDropDown(DropDown):
    @property
    def app(self):
        return session.app

    def set_language(self, lang):
        logging.debug(f"Dropdown: {self.dismiss_on_select=}")
        logging.debug(f"Dropdown: {self.auto_dismiss=}")
        logging.info(f"App: User chose UI language: {lang}")
        langfile.touch()
        if self.app.root.ids.lang.text != lang:
            langfile.write_text(lang)
            AppRestartPopup().open()
        self.dismiss()
