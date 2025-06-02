import locale


class Session:
    lang: str = f"{locale.getlocale()[0][:2]}"
    maclist: list = list()
    puzzlelist: list = list()
    puzzle = None
    packetlist: list = list()
