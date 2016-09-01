#!/bin/bash

export PATH=$PATH:~/node_modules/jpm/bin:/usr/local/vee/packages/homebrew/bin
exec jpm sign --api-key "$FIREFOX_API_KEY" --api-secret "$FIREFOX_API_SECRET"

