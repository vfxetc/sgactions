#!/usr/bin/env python

import json
import struct
import sys
import traceback
import subprocess


def log(*args):
    sys.stderr.write('[SGActions] %s\n' % ' '.join(str(x) for x in args))
    sys.stderr.flush()



handlers = {}

def handler(func):
    handlers[func.__name__] = func
    return func


def reply(orig, **msg):
    msg['dst'] = orig.get('src') or orig
    send(**msg)


def send(**msg):
    msg['src'] = 'native'
    encoded_msg = json.dumps(msg)
    sys.stdout.write(struct.pack('I', len(encoded_msg)))
    sys.stdout.write(encoded_msg)
    sys.stdout.flush()


@handler
def hello(**kw):
    reply(kw,
        type='hello',
        capabilities={'dispatch': True}
    )

@handler
def dispatch(url, **kw):
    log('dispatching', url)
    proc = subprocess.Popen(['python', '-m', 'sgactions.dispatch', url], stdout=sys.stderr)


while True:

    raw_size = sys.stdin.read(4)
    if not raw_size:
        # We are being shut down!
        break

    try:
        size, = struct.unpack('I', raw_size)
        raw_msg = sys.stdin.read(size)
        msg = json.loads(raw_msg)
    except Exception as e:
        log('exception during message reading:')
        traceback.print_exc()
        continue

    log('message:', json.dumps(msg, sort_keys=True))

    if msg.get('type') in handlers:
        try:
            handlers[msg['type']](**msg)
        except Exception as e:
            log('exception during message handling:')
            traceback.print_exc()
    else:
        log('unknown message type: %s' % msg.get('type'))

