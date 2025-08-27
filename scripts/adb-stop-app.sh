#!/usr/bin/env bash

# Kill app.
echo "Killing app [if running]."
adb shell am force-stop "io.github.tyounglightsys.network_puzzles"

# Kill logcat.
procs=$(ps aux | grep 'adb logcat' | grep -v grep | tr -s ' ' | cut -d' ' -f2)
for proc in $procs; do
    echo "Killing 'adb logcat' proc: $proc"
    kill $proc
done
