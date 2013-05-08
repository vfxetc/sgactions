import os
import sys
from subprocess import call

import shotgun_api3


def notify(message, title=None, sticky=False):
    
    if title is None:
        title = 'SGActions'

    print '=' * len(str(title))
    print str(title)
    print '=' * len(str(title))
    print message
    print '---'
    
    if sys.platform.startswith('darwin'):
        argv = ['growlnotify',
            '--name', 'Shotgun Action Dispatcher',
            '--title', title,
            '--message', message
        ]
        if sticky:
            argv.append('-s')
    else:
        argv = ['notify-send']
        if sticky:
            argv.extend(['-t', '3600000'])
        argv.extend([title, message])
    call(argv)


def get_shotgun(*args, **kwargs):

    if ('SHOTGUN_SERVER' in os.environ and
        'SHOTGUN_SCRIPT_NAME' in os.environ and
        'SHOTGUN_SCRIPT_KEY' in os.environ):
        return shotgun_api3.Shotgun(
            os.environ['SHOTGUN_SERVER'],
            os.environ['SHOTGUN_SCRIPT_NAME'],
            os.environ['SHOTGUN_SCRIPT_KEY'],
        )

    try:
        import shotgun_api3_registry
    except ImportError:
        raise RuntimeError("Set $SHOTGUN_API3_ARGS or provide shotgun_api3_registry.connect()")
    else:
        return shotgun_api3_registry.connect(*args, **kwargs)

