#!/bin/bash

errorcount=0

function test_one_file {
    filename=$1
    reversed=$(echo $filename | grep -v NOT)
    echo -n "testing $filename: "
    result=$(cat $filename | python -m src.network_puzzles | grep -i Congratulations)
    if [ -z "$result" ]; then
        if [ -z "$reversed" ]; then
            passed=true
        else
            passed=false
        fi
    else
        if [ -z "$reversed" ]; then
            passed=false
        else
            passed=true
        fi
    fi
    if $passed; then
        echo "OK"
        return 0
    else
        echo "Failed"
        return 1
    fi
}

function expand_file {
    totest="$1"
    find tests/solutions | grep -i "$1"
}

if [ $# -eq 0 ]; then
    #ls tests/solutions/* | while read filename; do
    for filename in tests/solutions/*; do
        test_one_file $filename
        myerror=$?
        errorcount=$(( $errorcount + $myerror))
    done
else
    #we have some command-line parameters.  Hopefully they are puzzle names
    while [ $# -gt 0 ]; do
        grabfiles=$(expand_file $1)
        shift
        for onefile in $grabfiles; do
            test_one_file $onefile
            myerror=$?
            errorcount=$(( $errorcount + $myerror))
        done
    done
fi
exit $errorcount
