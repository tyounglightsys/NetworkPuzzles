import gettext
import locale
from pathlib import Path

from .vars import Session


current_lang = locale.getlocale()[0]
localedir = Path(__file__).parent / 'resources' / 'locale'
t = gettext.translation('networkpuzzles', localedir=localedir, fallback=True, languages=[current_lang, "en"])
_ = t.gettext

__version__ = '0.1'

session = Session()