import json
import os

native_name = 'com.vfxetc.sgactions'
ext_path = os.path.abspath(os.path.join(__file__, '..', '..', 'browsers', 'webext'))


def get_native_messenger_origins(native_dir):
    native_path = os.path.join(native_dir, native_name + '.json')
    if os.path.exists(native_path):
        print '\t' + native_path
        try:
            existing = json.load(open(native_path))
            return existing['allowed_origins']
        except ValueError:
            pass
    
    return ()


def install_native_messenger(native_dir, allowed_extensions=None, allowed_origins=None):

    if not (allowed_origins or allowed_extensions):
        raise ValueError("One or allowed_extensions (Firefox) or allowed_origins (Chrome) required.")

    native_path = os.path.join(native_dir, native_name + '.json')
    print "\t" + native_path

    if not os.path.exists(native_dir):
        try:
            os.makedirs(native_dir)
        except OSError as e:
            print "\t\tCANNOT MKDIR:", e
            return

    try:
        fh = open(native_path, 'wb')
    except IOError as e:
        print "\t\tCANNOT WRITE:", e
        return

    data = {
        'name': native_name,
        'description': "SGActions dispatcher",
        'path': os.path.abspath(os.path.join(ext_path, '..', 'native', 'sgactions-native-messenger')),
        'type': 'stdio',
    }
    if allowed_extensions:
        data['allowed_extensions'] = allowed_extensions
    if allowed_origins:
        data['allowed_origins'] = allowed_origins

    with fh:
        fh.write(json.dumps(data))
