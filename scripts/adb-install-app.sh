#!/usr/bin/env bash

apk=
app_name="io.github.tyounglightsys.network_puzzles"
tempdir=$(mktemp -d)

function script_exit() {
    if [[ -d "$tempdir" ]]; then
        rm -r "$tempdir"
    fi
    exit $1
}


# Ensure infile given.
if [[ -f "$1" ]]; then
    infile="$1"
else
    echo "Error: Must provide path to package.zip or NetworkPuzzles APK file"
    script_exit 1
fi

# Define APK file.
if [[ ${infile##*.} == 'zip' ]]; then
    unzip -d "$tempdir" "$infile"
    apk=$(find "$tempdir" -name "*.apk" | sort -r | head -n1)
elif [[ ${infile##*.} = 'apk' ]]; then
    apk="$infile"
else
    echo "Error: Invalid input file: $infile"
    script_exit 1
fi

# Install APK file.
if [[ -f "$apk" ]]; then
    # Remove package if already installed.
    if [[ -n $(adb shell pm list packages "$app_name") ]]; then
        adb uninstall "$app_name"
    fi
    adb install "$apk"
else
    echo "Error: No APK file defined."
    script_exit 1
fi

script_exit 0
