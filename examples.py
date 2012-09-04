import os


def dump_kwargs(**kwargs):
    for k, v in sorted(kwargs.iteritems()):
        print '%s = %r' % (k, v)


def dump_environ(**kwargs):
    for k, v in sorted(os.environ.iteritems()):
        print '%s = %r' % (k, v)

