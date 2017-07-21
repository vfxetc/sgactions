#!/usr/bin/env python

from Queue import Queue
from warnings import warn
import functools
import json
import os
import re
import struct
import subprocess
import sys
import threading
import traceback
import weakref


from sgactions.dispatch import dispatch as _dispatch


def log(*args):
    sys.stderr.write('[SGActions] %s\n' % ' '.join(str(x) for x in args))
    sys.stderr.flush()

# We need to keep checking for this as long as the old Firefox plugin is
# in the wild.
_line_based = os.environ.get('SGACTIONS_HOST') == 'Firefox'

_capabilities = {}
_handlers = {}
_threads = weakref.WeakValueDictionary()
_local = threading.local()


def reply(orig, **msg):
    msg['dst'] = orig.get('src') or orig
    send(**msg)

def send(**msg):
    msg['src'] = 'native'
    encoded_msg = json.dumps(msg)
    log('send', len(encoded_msg), encoded_msg)
    if _line_based:
        sys.__stdout__.write(encoded_msg + '\n')
    else:
        sys.__stdout__.write(struct.pack('I', len(encoded_msg)))
        sys.__stdout__.write(encoded_msg)
    sys.__stdout__.flush()

def format_exception(e):
    return dict(type='error', error_type=e.__class__.__name__, error=str(e))

def reply_exception(orig, e):
    reply(orig, **format_exception(e))


def handler(func, name=None):
    if isinstance(func, basestring):
        return functools.partial(handler, name=func)
    _handlers[name or func.__name__] = func
    return func


@handler
def hello(capabilities=None, **kw):
    _capabilities.update(capabilities or {})
    reply(kw,
        type='elloh',
        capabilities={'dispatch': True},
        executable=sys.executable,
        script=__file__,
        native=os.environ.get('SGACTIONS_NATIVE'),
        origin=os.environ.get('SGACTIONS_ORIGIN'),
        host=os.environ.get('SGACTIONS_HOST'),
    )

@handler
def elloh(**kw):
    pass


@handler
def ping(**req):
    res = req.copy()
    res['type'] = 'pong'
    reply(req, res)

@handler
def pong(**kw):
    pass


@handler
def dispatch(url, **kw):
    log('dispatching:', url)
    res = _dispatch(url, reload=None)
    if isinstance(res, Exception):
        reply_exception(kw, res)
    else:
        reply(kw, type='result', result=res)


def send_and_recv(**kwargs):
    session = current_session()
    queue = session.get('result_queue')
    if not queue:
        queue = session['result_queue'] = Queue(1)
    timeout = kwargs.pop('timeout', 300)
    send(dst=session['src'], session_token=session['token'], **kwargs)
    reply = queue.get(timeout=timeout)
    log('async response:', repr(reply))
    return reply


@handler
def user_response(session_token, **kw):
    thread = _threads.get(session_token)
    if not thread:
        raise ValueError('no matching thread', session_token)
    session = thread.session
    queue = session.get('result_queue')
    if not queue:
        raise ValueError('session not expecting result', session_token)
    queue.put(kw, block=False)


def main():

    # We need to take over stdout so that print statements don't result in the
    # browser thinking it is getting a message back.
    sys.stdout = open('/tmp/sgactions.native.log', 'a')

    dispatch_counter = 0

    log('entering main loop')

    while True:

        try:

            if _line_based:
                raw_msg = sys.stdin.readline()
                if not raw_msg:
                    log('native port closed')
                    break

            else:
                raw_size = sys.stdin.read(4)
                if not raw_size:
                    log('native port closed')
                    break
                size, = struct.unpack('I', raw_size)
                log('reading message of size', raw_size)
                raw_msg = sys.stdin.read(size)

            msg = json.loads(raw_msg)

        except Exception as e:
            traceback.print_exc()
            send(**format_exception(e))
            continue

        if len(_threads):
            log('%d sessions already open' % len(_threads))

        if msg.get('type') not in _handlers:
            reply(msg, type='error', error='unknown message type %r' % msg.get('type'))
            log('unknown message type: %s' % msg.get('type'))

        dispatch_counter += 1

        thread = _threads[dispatch_counter] = threading.Thread(target=_dispatch_target, args=[msg])
        thread.daemon = True
        thread.session = {
            'type': msg['type'],
            'src': msg.get('src'),
            'token': dispatch_counter,
        }
        thread.start()
        del thread # Kill this reference immediately.


def current_session(strict=True):
    try:
        return threading.current_thread().session
    except AttributeError:
        if strict:
            raise RuntimeError('no current native handler')


def _dispatch_target(msg):
    try:
        _handlers[msg['type']](**msg)
    except Exception as e:
        traceback.print_exc()
        try:
            reply_exception(msg, e)
        except Exception as e:
            # Just in case it is the exception reporting mechanism...
            log('exception during reply_exception')
            traceback.print_exc()

