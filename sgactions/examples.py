import json
import os

from . import utils
from .browsers.native import is_native


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
        os._exit(0)
    else:
        utils.alert(message='Not the native messenger.')


def prompt_confirm(**kwargs):
    res = utils.confirm(
        title='Testing Shotgun Actions',
        message='Do you want to do the thing?',
    )
    utils.notify('You pressed "%s"' % ('OK' if res else 'Cancel'))


def prompt_select(**kwargs):
    res = utils.select(
        title='Testing Shotgun Actions',
        prologue="What is your favourite colour?",
        options=[(x, x) for x in 'Red', 'Orange', 'Yellow', 'Other'],
        epilogue="Just imagine that they are all listed here...",
    )
    utils.notify('You picked %s' % ('"%s"' % res if res else 'nothing'))
