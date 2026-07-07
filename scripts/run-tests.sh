#!/usr/bin/env bash

# Allow execution on headless system.
export KIVY_DPI=96
export KIVY_METRICS_DENSITY=1
export KIVY_METRICS_FONTSCALE=1
# Prevent windows from opening.
export KIVY_WINDOW=dummy
# Silence Kivy logging.
export KIVY_LOG_MODE=MIXED  # splits Kivy and Python logging
export KIVY_NO_CONSOLELOG=1  # turns off Kivy's console output

if [[ $1 == '-v' ]]; then
    python -m unittest -v
else
    python -m unittest -fb
fi
