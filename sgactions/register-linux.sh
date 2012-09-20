#!/usr/bin/env bash
#
#    This script attempts to register a protocol hander for
#    links that look like sgaction://blah.  
#
#    It should be sufficient for gnome apps like pidgin and kde apps
#    like konqueror.  Firefox seems to pay attention to the gnome
#    settings at least to the degree that it recognizes links of the
#    form $protocol://blah as hot-links, but it may still ask you to
#    select the application the first time you click on one.


protocol=sgaction
handler="python -m sgactions.dispatch"


echo "Installing $protocol protocol handler for Gnome."

gconfTool="$(which gconftool-2)"
if [[ "$gconfTool" ]]; then
    gconftool-2 --set --type=string /desktop/gnome/url-handlers/$protocol/command "$handler \"%s\""
    gconftool-2 --set --type=bool /desktop/gnome/url-handlers/$protocol/enabled true
    gconftool-2 --set --type=bool /desktop/gnome/url-handlers/$protocol/need-terminal false
else
    echo "WARNING: gconftool-2 not found: skipping gnome url-handler registration."
fi


echo "Installing $protocol protocol handler for KDE."

kdeProtoDir=~/.kde/share/services

if [[ "$KDEDIR" ]]; then
    kdeProtoDir="$KDEDIR/share/services"
fi

if [[ ! -e "$kdeProtoDir" ]]; then
    mkdir -p "$kdeProtoDir"
fi

if [[ -e "$kdeProtoDir" ]]; then
    kdeProtoFile="$kdeProtoDir/$protocol.protocol"
    rm -f $kdeProtoFile
    cat > $kdeProtoFile << EOF
[Protocol]
exec=$handler "%u"
protocol=$protocol
input=none
output=none
helper=true
listing=false
reading=false
writing=false
makedir=false
deleting=false
EOF
else
    echo "WARNING: can't find or create KDE protocol directory: $kdeProtoDir:  skipping KDE url-handler registration."
fi


echo "Done."
