import locale


class Session:
    lang = f"{locale.getlocale()[0][:2]}"
    maclist = list()
    puzzlelist = list()
    puzzle = dict()
    packetlist = list()
