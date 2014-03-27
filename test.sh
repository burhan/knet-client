#!/bin/sh

if ls Contributors.txt > /dev/null
then
    echo "Passed Contributors.txt test"
    exit 0
else
    echo "Failed the Contributors.txt test"
    exit 1
fi
