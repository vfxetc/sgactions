"""Register the protocol handler on various OSes."""

from subprocess import call, Popen, PIPE
import argparse
import hashlib
import json
import os
import re
import sys


from . import webext

sgactions_root = os.path.abspath(os.path.join(__file__, '..', '..', '..'))


_google_hash_map = {}
for i, c in enumerate('0123456789abcdef'):
    _google_hash_map[c] = chr(ord('a') + i)


def google_hash(text):
    digest = hashlib.sha256(text).hexdigest()[:32]
    return ''.join(_google_hash_map[x] for x in digest)


def setup_parser(parser):
    parser.what_group.add_argument('--chrome', action='store_true')


def install_chrome_extension(profile_dir, ext_path, force=False):

    prefs_path = os.path.join(profile_dir, 'Default', 'Preferences')
    
    if not os.path.exists(prefs_path):
        return
    print '\t' + profile_dir
    
    prefs = json.load(open(prefs_path))
    
    prefs_changed = False
    
    ext_rel_path = os.path.relpath(ext_path, os.path.abspath(os.path.join(__file__, '..', '..')))
    ext_id = google_hash(ext_path)

    # Remove all old extensions.
    for k, v in prefs['extensions']['settings'].items():
        if not isinstance(v, dict):
            continue
        if ext_rel_path in v.get('path', ''):
            if k == ext_id:
                print '\t\talready installed'
            else:
                print '\t\tremoving other:', v['path']
                del prefs['extensions']['settings'][k]
                prefs_changed = True
    
    # Install the extension.
    if force or ext_id not in prefs['extensions']['settings']:
        print '\t\tInstalling', ext_path
        prefs['extensions']['settings'][ext_id] = {
            "active_permissions": {
               "api": [ "nativeMessaging" ],
               "manifest_permissions": [  ],
               "scriptable_host": [ "https://*.shotgunstudio.com/*" ]
            },
            "commands": {

            },
            "content_settings": [  ],
            "creation_flags": 38,
            "events": [  ],
            "from_bookmark": False,
            "from_webstore": False,
            "granted_permissions": {
               "api": [ "nativeMessaging" ],
               "manifest_permissions": [  ],
               "scriptable_host": [ "https://*.shotgunstudio.com/*" ]
            },
            "incognito_content_settings": [  ],
            "incognito_preferences": {

            },
            "initial_keybindings_set": True,
            "install_time": "13078453141574979",
            "location": 4,
            "newAllowFileAccess": True,
            "path": ext_path,
            "preferences": {

            },
            "regular_only_preferences": {

            },
            "state": 1,
            "was_installed_by_default": False,
            "was_installed_by_oem": False
        }


        prefs_changed = True
    
    if prefs_changed:
        print '\t\tWriting changes'
        json.dump(prefs, open(prefs_path, 'w'), indent=4, sort_keys=True)





def main(args):

    if not (args.all or args.chrome):
        return
    
    ext_path = os.path.abspath(os.path.join(__file__, '..', '..', 'browsers', 'webext'))

    # Normalize so the same path on OS X and Linux; at WesternX lib and
    # lib64 are symlinked together.
    if '/lib64/' in ext_path:
        ext_path2 = ext_path.replace('/lib64/', '/lib')
        if os.path.exists(ext_path2):
            ext_path = ext_path2

    ext_paths = set((ext_path, os.path.realpath(ext_path)))

    for home in args.home:
        print('Setting up Chrome in', home)
        setup_one_home(home, args, ext_paths)

def setup_one_home(home, args, ext_paths):

    profile_dirs = [os.path.join(home, x) for x in (
        'Library/Application Support/Google/Chrome',
        'Library/Application Support/Chromium',
        '.config/google-chrome',
        '.config/chromium',
    )]
    for profile_dir in profile_dirs:
        # We don't know how to do this anymore.
        pass #install_chrome_extension(profile_dir, ext_path, force=args.force)

    native_dirs = [os.path.join(profile_dir, 'NativeMessagingHosts') for profile_dir in profile_dirs]
    # native_dirs.extend((
    #     '/Library/Google/Chrome/NativeMessagingHosts',
    #     '/Library/Application Support/Chromium/NativeMessagingHosts',
    # ) if sys.platform == 'darwin' else (
    #     '/etc/opt/chrome/native-messaging-hosts',
    #     '/etc/chromium/native-messaging-hosts',
    # ))

    print 'Finding existing native messengers...'
    native_origins = set("chrome-extension://%s/" % google_hash(ext_path) for ext_path in ext_paths)
    for native_dir in native_dirs:
        native_origins.update(webext.get_native_messenger_origins(native_dir))
    native_origins = list(sorted(native_origins))

    print 'Installing native messengers...'
    for native_dir in native_dirs:
        webext.install_native_messenger(native_dir, ext_path, native_origins)

    return True

