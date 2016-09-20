#!/bin/bash

if [[ ! "$FIREFOX_API_KEY" ]]; then
    echo 'You must set FIREFOX_API_KEY and FIREFOX_API_SECRET'
    exit 1
fi

export PATH=$PATH:~/node_modules/jpm/bin:/usr/local/vee/packages/homebrew/bin
exec jpm sign --api-key "$FIREFOX_API_KEY" --api-secret "$FIREFOX_API_SECRET"

