#!/usr/bin/env bash

# Create log file & redirect log output to it in the background.
app_name="io.github.tyounglightsys.network_puzzles"
log="${HOME}/${app_name}.log"
touch "$log"
adb logcat | grep -i python > "$log" &

# Start app.
adb shell am start -n "${app_name}/org.kivy.android.PythonActivity"
