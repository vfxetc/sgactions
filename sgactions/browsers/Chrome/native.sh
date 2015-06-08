#!/bin/bash

source ~/.bashrc

app_bundle="/usr/local/vee/Applications/SGActions.app/Contents/MacOS/SGActions"

if [[ -e "$app_bundle" ]]; then
    exec "$app_bundle" --chrome-native
else
    exec python "$(dirname "$0")"/../chrome_native.py
fi
