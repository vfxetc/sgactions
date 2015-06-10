#!/bin/bash

# Source the environment, but leave it as is if there is already something
# there so that dev-mode works.
if [[ "$VEE" == "" && "$KS_TOOLS" == "" ]]; then
	echo "[SGActions] sourcing environment" >&2
	source ~/.bashrc
fi

# Debugging info; gets sent to the console.
export SGACTIONS_NATIVE_SH="$0"
export SGACTIONS_EXT_ID="$1"

# Always load the Python that is associated with this version of sgactions.
# If sgactions was registered in dev mode, that will result in the dev
# code being called.
export PYTHONPATH="$(dirname $0)/../../..:$PYTHONPATH"

# Run within the application bundle on OS X so that notifications are
# easier to deal with.
app_bundle="/usr/local/vee/Applications/SGActions.app/Contents/MacOS/SGActions"
if [[ -e "$app_bundle" ]]; then
    exec "$app_bundle" --chrome-native
else
    exec python -m sgactions.browsers.chrome_native
fi
