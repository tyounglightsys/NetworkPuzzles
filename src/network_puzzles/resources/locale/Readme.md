## Updating Locales

1. Ensure that EN text in `./src/network_puzzles/messages.py` is correct.
1. Populate *gettext* PO (text) files
    ```
    $ ./scripts/update-locales.sh po # gathers strings from *.py and *.kv files
    $ ls -1 ./src/network_puzzles/resources/locale/*.po
    src/network_puzzles/resources/locale/en.po
    src/network_puzzles/resources/locale/fr.po
    ```
1. Translate EN text into FR in `fr.po`
1. Update *gettext* MO (binary) gettext files
    ```
    $ ./scripts/update-locales.sh mo
    ```
