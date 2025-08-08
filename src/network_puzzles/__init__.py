import argparse
import gettext
import logging
import sys
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
    "-f",
    "--filename",
    type=str,
    help="specify a different starting level instead of the default",
)
argparser.add_argument(
    "-v", "--verbose", action="store_true", help="show verbose output"
)

args, unknown_args = argparser.parse_known_args()
log_level = logging.WARNING
if sys.argv[0].endswith("test"):  # e.g. "python -m unittest"
    log_level = logging.CRITICAL
if args.verbose:
    log_level = logging.INFO
if args.debug:
    log_level = logging.DEBUG
if args.filename:
    session.startinglevel = args.filename

logging.basicConfig(
    level=log_level,
    format="%(levelname)s:%(filename)s:%(lineno)s:%(message)s",
)
