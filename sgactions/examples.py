import json
import os

from . import utils


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
