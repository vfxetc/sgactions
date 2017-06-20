from __future__ import print_function

import os
import sys
import subprocess
import shutil


PROTOCOL = 'sgaction'
HANDLER = 'python -m sgactions.dispatch'


def setup_parser(parser):
    parser.what_group.add_argument('--protocol', action='store_true',
        help="Install protocol handler.")


def main(args):

    if not (args.all or args.protocol):
        return

    _setup_gnome(args)

    for home in args.home:
        _setup_kde(home, args)

    return True


def _setup_gnome(args, protocol=PROTOCOL):

    if not sys.platform.startswith('linux'):
        return

    print("Installing {} protocol handler for Gnome.".format(protocol))

    has_gconftool = not subprocess.Popen(['which', '-q', 'gconftool-2']).wait()
    if not has_gconftool:
        print("WARNING: Cannot find gconftool-2.")
        return

    if args.dry_run:
        return

    subprocess.check_call(['gconftool-2', '--set', '--type=string',
        '/desktop/gnome/url-handlers/{}/command'.format(protocol),
        '{} "%s"'.format(HANDLER),
    ])
    subprocess.check_call(['gconftool-2', '--set', '--type=bool',
        '/desktop/gnome/url-handlers/{}/enabled'.format(protocol),
        'true',
    ])
    subprocess.check_call(['gconftool-2', '--set', '--type=bool',
        '/desktop/gnome/url-handlers/{}/need-terminal'.format(protocol),
        'false',
    ])



def _setup_kde(home, args, protocol=PROTOCOL):

    print("Installing {} protocol handler for KDE into {}".format(PROTOCOL, home))

    kde_dir = os.path.join(home, '.kde')
    if not os.path.exists(kde_dir):
        print("    NOTE: .kde does not exist; skipping.")
        return

    proto_dir = os.path.join(kde_dir, 'share/services')
    if not os.path.exists(proto_dir):
        os.makedirs(proto_dir)

    proto_path = os.path.join(proto_dir, protocol + '.protocol')
    with open(proto_path, 'wb') as fh:
        fh.write('''

[Protocol]
exec={handler} "%u"
protocol={protocol}
input=none
output=none
helper=true
listing=false
reading=false
writing=false
makedir=false
deleting=false

'''.strip().format(handler=HANDLER, protocol=protocol))

