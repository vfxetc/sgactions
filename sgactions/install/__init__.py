from __future__ import print_function

import argparse
import sys
import os

from . import chrome
from . import firefox
from . import protocol
from . import services


def main():

    parser = argparse.ArgumentParser()
    
    where_group = parser.add_argument_group('Location options')
    where_group.add_argument('-s', '--self', action='store_true',
        help="Install into my home.")
    where_group.add_argument('-S', '--self-dir', action='store_true',
        help="Install into all homes near mine.")
    where_group.add_argument('-d', '--home', action='append', default=[],
        help="Install into the given single user's home.")
    where_group.add_argument('-D', '--home-dir', action='append', default=[],
        help="Install into all homes in the given directory.")

    what_group = parser.what_group = parser.add_argument_group('Components to install')
    what_group.add_argument('-a', '--all', action='store_true',
        help="Install everything.")

    chrome.setup_parser(parser)
    firefox.setup_parser(parser)
    protocol.setup_parser(parser)
    services.setup_parser(parser)

    how_args = parser.add_argument_group('Runtime options')
    how_args.add_argument('-n', '--dry-run', action='store_true',
        help="Don't actually do anything.")
    how_args.add_argument('-f', '--force', action='store_true')
    how_args.add_argument('-x', '--experimental', action='store_true',
    	help="Include experimental features (e.g. Chrome install).")

    args = parser.parse_args()

    if args.self:
        args.home.append(os.path.expanduser('~'))
    if args.self_dir:
        args.home_dir.append(os.path.dirname(os.path.expanduser('~')))
    for home_dir in args.home_dir:
        for name in os.listdir(home_dir):
            if name.startswith('.'):
                continue
            args.home.append(os.path.join(home_dir, name))

    if not args.home:
        print("No installation directory specified.", file=sys.stderr)
        print("Please use one of --self, --home, or --home-dir.", file=sys.stderr)
        exit(2)

    did_something = False

    did_something = chrome.main(args) or did_something
    did_something = firefox.main(args) or did_something
    did_something = protocol.main(args) or did_something
    did_something = services.main(args) or did_something

    if not did_something:
        print("Nothing installed.", file=sys.stderr)


if __name__ == '__main__':
    main()


