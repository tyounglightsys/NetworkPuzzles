#!/bin/bash
ls tests/solutions/* | while read filename; do
    echo -n "testing $filename: "
    result=$(cat $filename | python -m src.network_puzzles | grep -i Congratulations)
    if [ -z "$result" ]; then
        echo "Failed"
    else
        echo "OK"
    fi
done
