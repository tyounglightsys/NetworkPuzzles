import argparse
import gettext
import logging
from pathlib import Path

from .vars import Session


session = Session()
localedir = Path(__file__).parent / "resources" / "locale"
t = gettext.translation(
    "networkpuzzles",
    localedir=localedir,
    fallback=True,
    languages=[str(session.locale), "en"],
)
_ = t.gettext

__version__ = "0.1"


argparser = argparse.ArgumentParser(prog="NetworkPuzzles")
argparser.add_argument("-d", "--debug", action="store_true", help="show debug output")
argparser.add_argument(
    "-v", "--verbose", action="store_true", help="show verbose output"
)

args = argparser.parse_args()
log_level = logging.WARNING
if args.verbose:
    log_level = logging.INFO
if args.debug:
    log_level = logging.DEBUG

logging.basicConfig(
    level=log_level,
    format="%(levelname)s:%(filename)s:%(lineno)s:%(message)s",
)
