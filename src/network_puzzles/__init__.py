import argparse
import gettext
import logging
import sys

from .vars import DATA_DIR, Session

__version__ = "0.1"

session = Session()
localedir = DATA_DIR / "resources" / "locale"
t_en = gettext.translation(
    "networkpuzzles",
    localedir=localedir,
    fallback=True,
    languages=["en"],
)
t_fr = gettext.translation(
    "networkpuzzles",
    localedir=localedir,
    fallback=True,
    languages=["fr", "en"],
)
match str(session.locale)[:2]:
    case "fr":
        t_fr.install()  # puts "_" func into global namespace
    case _:
        t_en.install()


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
if "unittest" in sys.argv:
    log_level = logging.CRITICAL
elif "-m" in sys.argv:  # CLI invokation
    log_level = logging.CRITICAL
if args.verbose:
    log_level = logging.INFO
if args.debug:
    log_level = logging.DEBUG
if args.filename:
    session.startinglevel = args.filename
    session.history.append(f"load {args.filename}")

logging.basicConfig(
    level=log_level,
    format="%(levelname)s:%(filename)s:%(lineno)s:%(message)s",
)

logging.debug(f"App: {sys.argv=}")
logging.debug(f"App: {localedir=}:")
for i in localedir.iterdir():
    logging.debug(f"App: - {i}")
logging.info(f"App: system locale: {session.locale}")
