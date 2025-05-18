#!/usr/bin/env bash

scripts_dir="$(dirname "$0")"
repo_dir="$(dirname "$scripts_dir")"
pkg_dir="${repo_dir}/src/network_puzzles"
locale_dir="${pkg_dir}/resources/locale"
messages_temp="${pkg_dir}/resources/locale/messages.pot"

usage(){
    echo "$0 po|mo"
    exit 1
}

if [[ $1 == po ]]; then
    xgettext -L python -o "$messages_temp" -D "${pkg_dir}" networkpuzzles.kv gui.py messages.py
    for lang in "en" "fr"; do
        msgmerge --update --no-fuzzy-matching --backup=off "${locale_dir}/${lang}.po" "$messages_temp"
    done
elif [[ $1 == mo ]]; then
    for lang in "en" "fr"; do
	    mkdir -p "${locale_dir}/${lang}/LC_MESSAGES"
	    msgfmt -c -o "${locale_dir}/${lang}/LC_MESSAGES/networkpuzzles.mo" "${locale_dir}/${lang}.po"
    done
else
    usage
fi
