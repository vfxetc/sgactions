SGActions Firefox Extension
===========================


Developing
----------

Getting started with JPM: https://developer.mozilla.org/en-US/Add-ons/SDK/Tools/jpm#Installation

As of Firefox 48, you can't use unsigned extensions in a branded Firefox. You need to develop in the "unbranded" or nightly builds. See: https://wiki.mozilla.org/Add-ons/Extension_Signing#Unbranded_Builds

Development is much easier with the [Extension Auto-Installer](https://addons.mozilla.org/en-US/firefox/addon/autoinstaller/), which the `watch.sh` script uses to update your extension whenever it is changed.

Then you can `dev /Applications/Nightly/Contents/MacOS/firefox` to develop.
