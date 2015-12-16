import json
import os

from . import utils
from .browsers.chrome_native import is_native


def dump_kwargs(**kwargs):
    utils.alert(
        title='%s Kwargs' % kwargs.get('entity_type', 'Unknown'),
        message='<pre>%s</pre>' % json.dumps(kwargs, sort_keys=True, indent=4)
    )


def dump_environ(**kwargs):
    utils.alert(
        title='%s Environ' % kwargs.get('entity_type', 'Unknown'),
        message='<pre>%s</pre>' % '\n'.join('%s=%s' % x for x in sorted(os.environ.iteritems())),
    )


def raise_error(**kwargs):
    raise ValueError('This is a test')

def disconnect(**kwargs):
    if is_native():
        exit(0)
    else:
        utils.alert(message='Not the native messenger.')

