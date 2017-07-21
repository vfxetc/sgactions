import logging
import os
import re
import sys
import tempfile
from subprocess import call, check_call, CalledProcessError
from warnings import warn

try:
    import shotgun_api3
except ImportError as e:
    pass


log = logging.getLogger(__name__)


def get_runtime():
    from .browsers.native import runtime
    return runtime


def notify(message, title=None, sticky=None, details=None, strict=False):

    if title is not None:
        warn('sgactions.utils.notify title is deprecated')
    if sticky is not None:
        warn('sgactions.utils.notify sticky is deprecated')

    try:
        get_runtime().notify(message, details=details, strict=strict)
    except RuntimeError:
        # We lose the details here, but meh.
        from uitools.notifications import Notification
        Notification(title or 'SGActions', message).send()

def alert(message, title=None, strict=False):
    title = title or 'SGActions'
    try:
        get_runtime().alert(message, title=title, strict=strict)
    except RuntimeError:
        from uitools.notifications import Notification
        Notification(title, message).send()

def progress(message, title=None, strict=False):
    if title is not None:
        warn('sgactions.utils.progress title is deprecated')
    try:
        get_runtime().progress(message, title, strict=strict)
    except RuntimeError:
        pass

def confirm(*args, **kwargs):
    return get_runtime().confirm(*args, **kwargs)


def select(*args, **kwargs):
    from .browsers.chrome_native import select
    return select(*args, **kwargs)


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
        raise RuntimeError("Set $SHOTGUN_{SERVER,SCRIPT_NAME,SCRIPT_KEY} or provide shotgun_api3_registry.connect()")
    else:
        return shotgun_api3_registry.connect(*args, **kwargs)


if __name__ == '__main__':
    notify('Test message', 'Test')
