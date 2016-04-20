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
export SGACTIONS_HOST="${2-Chrome}"

# Always load the Python that is associated with this version of sgactions.
# If sgactions was registered in dev mode, that will result in the dev
# code being called.
export PYTHONPATH="$(dirname $0)/../../..:$PYTHONPATH"

# We could use the app at /usr/local/vee/Applications/SGActions.app, but
# then it would always be the in dock. Instead, notifications may get a
# little messier.
exec python -m sgactions.browsers.chrome_native
