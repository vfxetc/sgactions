"""Register the protocol handler on various OSes."""

from subprocess import call, Popen, PIPE
import argparse
import hashlib
import json
import os
import re
import sys


sgactions_root = os.path.abspath(os.path.join(__file__, '..', '..'))


_google_hash_map = {}
for i, c in enumerate('0123456789abcdef'):
    _google_hash_map[c] = chr(ord('a') + i)


def google_hash(text):
    digest = hashlib.sha256(text).hexdigest()[:32]
    return ''.join(_google_hash_map[x] for x in digest)


def install_chrome_extension(profile_dir, ext_path, force=False):

    if not os.path.exists(profile_dir):
        return
    print '\t' + profile_dir

    prefs_path = os.path.join(profile_dir, 'Default', 'Preferences')
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


def get_native_messenger_origins(native_dir):
    native_path = os.path.join(native_dir, 'com.westernx.sgactions.json')
    if os.path.exists(native_path):
        print '\t' + native_path
        try:
            existing = json.load(open(native_path))
            return existing['allowed_origins']
        except ValueError:
            pass
    
    return ()


def install_native_messenger(native_dir, ext_path, native_origins):

    native_path = os.path.join(native_dir, 'com.westernx.sgactions.json')
    print '\t' + native_path

    if not os.path.exists(native_dir):
        try:
            os.makedirs(native_dir)
        except OSError as e:
            print '\t\tCANNOT MKDIR:', e
            return

    try:
        fh = open(native_path, 'wb')
    except IOError as e:
        print '\t\tCANNOT WRITE:', e
        return

    with fh:
        fh.write(json.dumps({
            "name": "com.westernx.sgactions",
            "description": "SGActions",
            "path": os.path.join(ext_path, 'native.sh'),
            "type": "stdio",
            "allowed_origins": native_origins,
        }))


def main():   

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', action='store_true')
    args = parser.parse_args()

    ext_path = os.path.abspath(os.path.join(__file__, '..', 'browsers', 'Chrome'))

    # Normalize so the same path on OS X and Linux; in our environment lib and
    # lib64 are symlinked together.
    if '/lib64/' in ext_path:
        ext_path2 = ext_path.replace('/lib64/', '/lib')
        if os.path.exists(ext_path2):
            ext_path = ext_path2

    ext_paths = set((ext_path, os.path.realpath(ext_path)))

    print 'installing Chrome extension:', ext_path
    profile_dirs = [os.path.expanduser(x) for x in (
        '~/Library/Application Support/Google/Chrome',
        '~/Library/Application Support/Google/Chrome Canary',
        '~/.config/google-chrome'
    )]
    for profile_dir in profile_dirs:
        install_chrome_extension(profile_dir, ext_path, force=args.force)

    native_dirs = [os.path.join(profile_dir, 'NativeMessagingHosts') for profile_dir in profile_dirs]
    native_dirs.extend((
        '/Library/Google/Chrome/NativeMessagingHosts',
        '/Library/Application Support/Chromium/NativeMessagingHosts',
    ) if sys.platform == 'darwin' else (
        '/etc/opt/chrome/native-messaging-hosts',
        '/etc/chromium/native-messaging-hosts',
    ))

    print 'finding existing native messengers'
    native_origins = set("chrome-extension://%s/" % google_hash(ext_path) for ext_path in ext_paths)
    for native_dir in native_dirs:
        native_origins.update(get_native_messenger_origins(native_dir))
    native_origins = list(sorted(native_origins))

    print 'installing native messenger'
    for native_dir in native_dirs:
        install_native_messenger(native_dir, ext_path, native_origins)

    if sys.platform.startswith("darwin"):

        print 'installing OS X services'
        our_services = os.path.join(sgactions_root, 'sgactions', 'platforms', 'darwin', 'Services')
        system_services = os.path.expanduser(os.path.join('~', 'Library', 'Services'))
        for service_name in os.listdir(our_services):

            if service_name.startswith('.'):
                continue
            print '\t' + service_name
            
            src = os.path.join(our_services, service_name)
            dst = os.path.join(system_services, service_name)
            
            # Try to make the folder first so that it puts it where I expect it to,
            # since I've been having issues with this copy.
            call(['mkdir', '-p', dst])
            call(['rsync', '-ax', '--delete', src + '/', dst + '/'])

        print 'refreshing services'
        call(['/System/Library/CoreServices/pbs', '-flush'])
    
    elif sys.platform.startswith('linux'):
        call([os.path.join(os.path.dirname(__file__), 'register-linux.sh')])


    print 'done'


if __name__ == '__main__':
    main()
