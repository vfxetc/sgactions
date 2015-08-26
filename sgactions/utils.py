import logging
import os
import re
import sys
import tempfile
from subprocess import call, check_call, CalledProcessError
from warnings import warn
import shotgun_api3


log = logging.getLogger(__name__)


def notify(message, title=None, sticky=None, details=None):
    
    if title is not None:
        warn('sgactions.utils.notify title is deprecated')
    if sticky is not None:
        warn('sgactions.utils.notify sticky is deprecated')

    try:
        from .browsers.chrome_native import notify
        notify(message, details=details)
    except RuntimeError:
        # We lose the details here, but meh.
        from uitools.notifications import Notification
        Notification(title or 'SGActions', message).send()


def alert(message, title=None):
    title = title or 'SGActions'
    try:
        from .browsers.chrome_native import alert
        alert(message, title=title)
    except RuntimeError:
        from uitools.notifications import Notification
        Notification(title, message).send()


def progress(message, title=None):
    
    if title is not None:
        warn('sgactions.utils.progress title is deprecated')
    try:
        from .browsers.chrome_native import progress
        progress(message, title)
    except RuntimeError:
        pass



def progress_cancelled():
    try:
        from .browsers.chrome_native import progress_cancelled
        return progress_cancelled()
    except RuntimeError:
        pass


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

