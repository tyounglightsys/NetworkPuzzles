#!/usr/bin/env bash
# Attempt to produce mobile experince from desktop.
# This potentially depends on several variables:
# - KIVY_METRICS_DENSITY; 0.75, 1, 1.5, 2 on android
# - KIVY_METRICS_FONTSCALE; 0.8 to 1.2 on android
# - KIVY_DPI; 96 for desktop, but 160, 240, 320, 480 are all possible on android
# Values used here are based on comparing with a Samsung Galaxy A13.
export KIVY_METRICS_DENSITY=1.9
scripts/run-desktop.sh $@
