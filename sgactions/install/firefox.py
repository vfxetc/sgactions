from __future__ import print_function

import os
import shutil
import sys


def setup_parser(parser):
    parser.what_group.add_argument('--firefox', action='store_true',
        help="Install Firefox addon.")
    firefox_group = parser.add_argument_group('Firefox options')
    firefox_group.add_argument('--xpi', default='/Volumes/CGroot/systems/packages/Firefox/sgactions/latest.xpi')


def main(args):

    if not (args.all or args.firefox):
        return

    if not os.path.exists(args.xpi):
        print("Firefox XPI does not exist.", file=sys.stderr)
        exit(1)

    for home in args.home:
        print('Setting up firefox in', home)
        setup_one_home(home, args)

    return True


def setup_one_home(home, args):

    count = 0

    for rel_profile in 'Library/Application Support/Firefox/Profiles', '.mozilla/firefox':
        profile_root = os.path.join(home, rel_profile)
        if not os.path.exists(profile_root):
            continue
        for name in os.listdir(profile_root):
            ext_dir = os.path.join(profile_root, name, 'extensions')
            if not os.path.exists(ext_dir):
                continue
            _copy_extension(ext_dir, args)
            count += 1

    if not count:
        print('    WARNING: No Firefox profiles found!')


def _copy_extension(ext_dir, args):
    dst = os.path.join(ext_dir, '@sgactions.xpi')
    print('    Copying extension to', dst)
    if not args.dry_run:
        if os.path.exists(dst):
            os.unlink(dst)
        shutil.copyfile(args.xpi, dst)