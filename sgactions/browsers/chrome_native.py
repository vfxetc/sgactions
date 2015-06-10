#!/usr/bin/env python

import json
import struct
import sys
import traceback
import subprocess

from ..dispatch import dispatch as _dispatch


def log(*args):
    sys.stderr.write('[SGActions] %s\n' % ' '.join(str(x) for x in args))
    sys.stderr.flush()


_handlers = {}

def handler(func):
    _handlers[func.__name__] = func
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

        if msg.get('type') in _handlers:
            try:
                _handlers[msg['type']](**msg)
            except Exception as e:
                traceback.print_exc()
                reply_exception(msg, e)
        else:
            reply(msg, type='error', error='unknown message type %r' % msg.get('type'))
            log('unknown message type: %s' % msg.get('type'))


if __name__ == '__main__':
    main()

