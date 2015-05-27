#!/usr/bin/env python

import json
import struct
import sys


def send(msg):
    msg = json.dumps(msg)
    sys.stdout.write(struct.pack('I', len(msg)))
    sys.stdout.write(msg)
    sys.stdout.flush()

send("native messaging start")

while True:

    raw_size  = sys.stdin.read(4)
    if not raw_size:
        break
    print >> sys.stderr, repr(raw_size)

    size, = struct.unpack('I', raw_size)

    print >> sys.stderr, repr(size)

    raw_msg = sys.stdin.read(size)
    msg = json.loads(raw_msg)

    print >> sys.stderr, 'got:', json.dumps(raw_msg)

    if msg.get('type') == 'hello':
        send({
            'src': 'native',
            'dst': msg['src'],
            'type': 'hello',
            'capabilities': ['open_url'],
        })

    else:
        send({
            'src': 'native',
            'dst': msg['src'],
            'type': 'error',
            'error': 'unknown type %r' % msg.get('type')
        })

