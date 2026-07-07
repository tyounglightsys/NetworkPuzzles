import re


def exclude_from_list(unfiltered_items: list, regexp: str):
    regexb = re.compile(regexp)
    return [i for i in unfiltered_items if not regexb.match(i)]
