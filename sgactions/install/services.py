from __future__ import print_function

import os
import sys
import subprocess
import shutil

def setup_parser(parser):
    parser.what_group.add_argument('--services', action='store_true',
        help="Install macOS services.")

def main(args):

    if not (args.all or args.services):
        return

    for home in args.home:
        _install_services(home, args)

    if sys.platform == 'darwin':
        print("Refreshing local services.")
        subprocess.check_call(['/System/Library/CoreServices/pbs', '-flush'])

    return True


def _install_services(home, args):

    sgactions_root = os.path.abspath(os.path.join(__file__, '..', '..', '..'))
    src_dir = os.path.join(sgactions_root, 'sgactions', 'platforms', 'darwin', 'Services')
    dst_dir = os.path.join(home, 'Library', 'Services')

    print("Installing macOS services into:", dst_dir)

    if not os.path.exists(dst_dir):
        print("    WARNING: directory doesn't exist.")
        return

    if args.dry_run:
        return

    service_names = os.listdir(src_dir)
    service_names = [x for x in service_names if not x.startswith('.')]

    for service_name in service_names:
        
        src = os.path.join(src_dir, service_name)
        dst = os.path.join(dst_dir, service_name)
        
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
