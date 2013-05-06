#!/bin/bash

# C0111: Ignore missing docstrings
PYLINT="pylint -d C0111 -d C0301"

for module in $(ls buildfarm/*.py); do
    $PYLINT $module 2>/dev/null > buildfarm/`basename $module`.pylint
done

for script in $(ls tools); do
    $PYLINT $script 2>/dev/null > tools/`basename $script`.pylint
done
