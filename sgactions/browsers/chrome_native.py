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
        capabilities={'dispatch': True},
        executable=sys.executable,
        file=__file__,
    )

@handler
def dispatch(url, **kw):
    cmd = [sys.executable, '-m', 'sgactions.dispatch', url]
    log('dispatching:', *cmd)
    proc = subprocess.Popen(cmd, stdout=sys.stderr)


def main():

    sys.stderr = open('/tmp/sgactions.native.log', 'a')

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


if __name__ == '__main__':
    main()

