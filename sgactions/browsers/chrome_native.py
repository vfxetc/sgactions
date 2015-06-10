#!/usr/bin/env python

import functools
import json
import struct
import subprocess
import sys
import traceback

# This must be absolute, since this script is run directly in Linux.
from sgactions.dispatch import dispatch as _dispatch


def log(*args):
    sys.stderr.write('[SGActions] %s\n' % ' '.join(str(x) for x in args))
    sys.stderr.flush()

_current_source = None
_handlers = {}

def handler(func, name=None):
    if isinstance(func, basestring):
        return functools.partial(handler, name=func)
    _handlers[name or func.__name__] = func
    return func

def reply(orig, **msg):
    msg['dst'] = orig.get('src') or orig
    msg['src'] = 'native'
    send(**msg)

def send(**msg):
    msg['src'] = 'native'
    encoded_msg = json.dumps(msg)
    log('send', len(encoded_msg), encoded_msg)
    sys.__stdout__.write(struct.pack('I', len(encoded_msg)))
    sys.__stdout__.write(encoded_msg)
    sys.__stdout__.flush()

def format_exception(e):
    return dict(type='error', error_type=e.__class__.__name__, error=str(e))

def reply_exception(orig, e):
    reply(orig, **format_exception(e))


@handler
def hello(**kw):
    reply(kw,
        type='hello',
        capabilities={'dispatch': True},
        executable=sys.executable,
        file=__file__,
    )


@handler
def dispatch(url, **kw):
    log('dispatching:', url)
    res = _dispatch(url, reload=None)
    if isinstance(res, Exception):
        reply_exception(kw, res)
    else:
        reply(kw, type='result', result=res)


def main():

    global _current_source

    # We need to take over both stdout and stderr so that print statements
    # don't result in chrome thinking it is getting a message back.
    sys.stdout = sys.stderr = open('/tmp/sgactions.native.log', 'a')

    while True:

        raw_size = sys.stdin.read(4)
        if not raw_size:
            print >> sys.stderr, '[SGActions] native port closed'
            break

        try:
            size, = struct.unpack('I', raw_size)
            raw_msg = sys.stdin.read(size)
            msg = json.loads(raw_msg)
        except Exception as e:
            traceback.print_exc()
            send(**format_exception(e))
            continue

        log('recv', size, raw_msg)

        _current_source = msg.get('src')
        _progress_cancelled = None

        if msg.get('type') in _handlers:
            try:
                _handlers[msg['type']](**msg)
            except Exception as e:
                traceback.print_exc()
                reply_exception(msg, e)
        else:
            reply(msg, type='error', error='unknown message type %r' % msg.get('type'))
            log('unknown message type: %s' % msg.get('type'))

    _running = False


# For runtime!
def alert(message, title=None):
    if _current_source:
        send(dst=_current_source, type='alert', title=title, message=message)
    else:
        raise RuntimeError('no current native handler')

def progress(message, title=None):
    if _current_source:
        send(dst=_current_source, type='progress', title=title, message=message)
    else:
        raise RuntimeError('no current native handler')

@handler('progress_cancelled')
def on_progress_cancelled(**msg):
    progress_cancelled(True)

_progress_cancelled = None
def progress_cancelled(value=None):
    global _progress_cancelled
    if value is not None:
        _progress_cancelled = value
    return _progress_cancelled


if __name__ == '__main__':
    main()

