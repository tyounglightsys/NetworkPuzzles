import gettext
from pathlib import Path

from .vars import Session


session = Session()
localedir = Path(__file__).parent / 'resources' / 'locale'
t = gettext.translation('networkpuzzles', localedir=localedir, fallback=True, languages=[session.locale, "en"])
_ = t.gettext

__version__ = '0.1'
