SGActions Firefox Extension
===========================


Developing
----------

Getting started with JPM: https://developer.mozilla.org/en-US/Add-ons/SDK/Tools/jpm#Installation

As of Firefox 48, you can't use unsigned extensions in a branded Firefox. You need to develop in the "unbranded" or nightly builds. See: https://wiki.mozilla.org/Add-ons/Extension_Signing#Unbranded_Builds

Development is much easier with the [Extension Auto-Installer](https://addons.mozilla.org/en-US/firefox/addon/autoinstaller/), which the `watch.sh` script uses to update your extension whenever it is changed.

Then you can `dev /Applications/Nightly/Contents/MacOS/firefox` to develop.


Signing
-------

Extensions must be signed to be deployed to standard Firefox. The extension is currenlty owned by `mozilla-addons@mikeboers.com`. The extension can be signed by:

```
export FIREFOX_API_KEY=xxx
export FIREFOX_API_SECRET=yyy
./sign.sh
```

Don't forget that Mozilla requires a unique SemVer version for every new signature.


Deployment
----------

We have a few options to deploy:

1. List the addon publically. I'm not keen on dealing with the vetting process at this time.
2. Host it somewhere ourselves. We need to host the updates via HTTPS (which we can't do internally at this time), or some other crypto nonsense.
3. Install into the `Firefox.app` (and similar on Linux) and the user's profile(s) in their home. This presents them with the dialog the first time they open Firefox, and then updates are allowed afterwards.
