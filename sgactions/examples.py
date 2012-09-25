import os

from . import utils


def dump_kwargs(**kwargs):
    utils.notify(
        title='%s Kwargs' % kwargs.get('entity_type', 'Unknown'),
        message='\n'.join('%s = %r' % x for x in sorted(kwargs.iteritems())),
        sticky=True,
    )


def dump_environ(**kwargs):
    utils.notify(
        title='%s Environ' % kwargs.get('entity_type', 'Unknown'),
        message='\n'.join('%s = %r' % x for x in sorted(os.environ.iteritems())),
        sticky=True,
    )


def raise_error(**kwargs):
    raise ValueError('This is a test')
