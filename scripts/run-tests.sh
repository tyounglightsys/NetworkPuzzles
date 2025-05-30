#!/usr/bin/env bash

if [[ $1 == '-v' ]]; then
    python -m unittest -v
else
    python -m unittest -b
fi
