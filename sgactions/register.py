"""Register the protocol handler on various OSes."""

from subprocess import call, Popen, PIPE
import os
import sys
import re
import json
import hashlib


sgactions_root = os.path.abspath(os.path.join(__file__, '..', '..'))


_google_hash_map = {}
for i, c in enumerate('0123456789abcdef'):
    _google_hash_map[c] = chr(ord('a') + i)


def google_hash(text):
    digest = hashlib.sha256(text).hexdigest()[:32]
    return ''.join(_google_hash_map[x] for x in digest)


def install_chrome_extension(path):
    
    if not os.path.exists(path):
        return
    print '\tChecking', path
    prefs = json.load(open(path))
    
    changed = False
    
    ext_path = os.path.abspath(os.path.join(__file__, '..', 'browsers', 'Chrome'))
    ext_rel_path = os.path.relpath(ext_path, os.path.abspath(os.path.join(__file__, '..', '..')))
    ext_id = google_hash(ext_path)
    
    # Remove all old extensions.
    for k, v in prefs['extensions']['settings'].items():
        if ext_rel_path in v.get('path', ''):
            if k == ext_id:
                print '\t\tAlready installed'
            else:
                print '\t\tRemoving other:', v['path']
                del prefs['extensions']['settings'][k]
                changed = True
    
    # Install the extension.
    if ext_id not in prefs['extensions']['settings']:
        print '\t\tInstalling', ext_path
        prefs['extensions']['settings'][ext_id] = {
           "active_permissions": {
              "scriptable_host": [ "https://*.shotgunstudio.com/*" ]
           },
           "events": [ "runtime.onInstalled" ],
           "from_bookmark": False,
           "from_webstore": False,
           "granted_permissions": {
              "scriptable_host": [ "https://*.shotgunstudio.com/*" ]
           },
           "install_time": "12992636740554400",
           "location": 4,
           "newAllowFileAccess": True,
           "path": ext_path,
           "state": 1
        }
        changed = True
    
    # Install the native messenger
    native_dir = os.path.expanduser(
        '~/Library/Application Support/Google/Chrome/NativeMessagingHosts'
        if sys.platform == 'darwin' else
        '~/.config/google-chrome/NativeMessagingHosts'
    )
    native_path = os.path.join(native_dir, 'com.keypics.sgactions.json')
    if changed or not os.path.exists(native_path):
        print '\tInstalling native messenger', native_path
        if not os.path.exists(native_dir):
            os.makedirs(native_dir)
        with open(native_path, 'wb') as fh:
            fh.write(json.dumps({
                "name": "com.keypics.sgactions",
                "description": "SGActions",
                "path": os.path.join(ext_path, 'native.sh'),
                "type": "stdio",
                "allowed_origins": [
                    "chrome-extension://%s/" % ext_id,
                ],
            }))

    if changed:
        print '\t\tWriting changes...'
        json.dump(prefs, open(path, 'w'), indent=4, sort_keys=True)



    
def main():

    if sys.platform.startswith('linux'):
        # All of the logic is in a shell script.
        call([
            os.path.join(os.path.dirname(__file__), 'register-linux.sh'),
        ])        

    print 'Installing Chrome extension...'
    install_chrome_extension(os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Preferences'))
    install_chrome_extension(os.path.expanduser('~/Library/Application Support/Google/Chrome Canary/Default/Preferences'))
    install_chrome_extension(os.path.expanduser('~/.config/google-chrome/Default/Preferences'))
    print 'Done.'
    
    print 'Installing OS X Services...'
    
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
        
    if sys.platform.startswith("darwin"):
        print 'Refreshing services...'
        call(['/System/Library/CoreServices/pbs', '-flush'])
    
    print 'Done.'


if __name__ == '__main__':
    main()
