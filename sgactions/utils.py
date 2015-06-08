import os
import re
import sys
import tempfile
from subprocess import call, check_call, CalledProcessError

import shotgun_api3


def notify(message, title=None, sticky=False):
    
    from uitools.notifications import Notification

    if title is None:
        title = 'SGActions'

    print '=' * len(str(title))
    print str(title)
    print '=' * len(str(title))
    print message
    print '---'
    
    Notification(title, message).send()


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


if __name__ == '__main__':
    notify('Test message', 'Test')

