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

if __name__ == '__main__':
    sys.modules['sgactions.browsers.chrome_native'] = sys.modules['__main__']


def log(*args):
    sys.stderr.write('[SGActions] %s\n' % ' '.join(str(x) for x in args))
    sys.stderr.flush()

_active_threads = {}
_capabilities = {}
_current_source = None
_handlers = {}
_confirm_queues = {}

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


def start_thread(target, args=None, kwargs=None, **other):
    thread = threading.Thread(target=_handle_thread, args=(target, args or (), kwargs or {}), **other)
    _active_threads[thread] = (target, args, kwargs)
    thread.daemon = True
    thread.start()
    return thread

def _handle_thread(func, args, kwargs):
    try:
        func(*args, **kwargs)
    finally:
        _active_threads.pop(threading.current_thread(), None)


@handler
def hello(capabilities=None, **kw):
    _capabilities.update(capabilities or {})
    reply(kw,
        type='elloh',
        capabilities={'dispatch': True},
        executable=sys.executable,
        script=__file__,
        bootstrapper=os.environ.get('SGACTIONS_NATIVE_SH'),
        extension=os.environ.get('SGACTIONS_EXT_ID'),
    )


@handler
def dispatch(url, **kw):
    log('dispatching in thread:', url)
    start_thread(_dispatch_target, args=(url, kw))

def _dispatch_target(url, kw):
    res = _dispatch(url, reload=None)
    if isinstance(res, Exception):
        reply_exception(kw, res)
    else:
        reply(kw, type='result', result=res)


@handler
def user_response(session, **kw):
    queue = _confirm_queues.pop(session)
    queue.put(kw)


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

        if msg.get('type') not in _handlers:
            reply(msg, type='error', error='unknown message type %r' % msg.get('type'))
            log('unknown message type: %s' % msg.get('type'))

        try:
            _handlers[msg['type']](**msg)
        except Exception as e:
            traceback.print_exc()
            try:
                reply_exception(msg, e)
            except Exception as e:
                # Just in case it is the exception reporting mechanism...
                print >> sys.stderr, 'EXCEPTION DURING reply_exception'
                traceback.print_exc()


    _running = False


# For runtime!

def is_native():
    return bool(_current_source)

def alert(message, title=None, strict=False):
    if _current_source:
        send(dst=_current_source, type='alert', title=title, message=message)
    elif strict:
        raise RuntimeError('no current native handler')

def progress(message, title=None, strict=False):
    if title is not None:
        warn('sgactions.browsers.chrome_native.progress title is deprecated')
    if _current_source:
        send(dst=_current_source, type='progress', message=message)
    elif strict:
        raise RuntimeError('no current native handler')

def notify(message, details=None, strict=False):
    if _current_source:
        send(dst=_current_source, type='notify', message=message, details=details)
    elif strict:
        raise RuntimeError('no current native handler')

def confirm(message, title=None, default=None):

    if not _current_source:
        if default is not None:
            return default
        raise RuntimeError('no current native handler')
    if not _capabilities.get('confirm'):
        if default is not None:
            return default
        raise RuntimeError('confirm is not supported by native handler')

    queue = Queue(1)
    session = os.urandom(8).encode('hex')
    _confirm_queues[session] = queue

    send(dst=_current_source, type='confirm', message=message, title=title,
        session=session)

    reply = queue.get()
    log(repr(reply))
    return reply['value']


def select(options, prologue=None, epilogue=None, title=None, default=None):

    if not _current_source:
        if default is not None:
            return default
        raise RuntimeError('no current native handler')
    if not _capabilities.get('select'):
        if default is not None:
            return default
        raise RuntimeError('select is not supported by native handler')

    # Normalize all of the options.
    options = list(options)
    for i, option in enumerate(options):
        if isinstance(option, basestring):
            option = {'name': option, 'label': option}
        if isinstance(option, (tuple, list)):
            option = {'name': option[0], 'label': option[1]}
        else:
            option = dict((key, option[key]) for key in ('name', 'label'))
        if not re.match(r'[\w-]+$', option['name']):
            raise ValueError('option name has special characters', option['name'])
        options[i] = option
        option['checked'] = option['name'] == default

    queue = Queue(1)
    session = os.urandom(8).encode('hex')
    _confirm_queues[session] = queue

    send(dst=_current_source, type='select', options=options, title=title,
        prologue=prologue, epilogue=epilogue,
        session=session)

    reply = queue.get()
    log(repr(reply))

    value = reply['value']
    if value is None:
        return default
    return value



@handler('progress_cancelled')
def on_progress_cancelled(**msg):
    progress_cancelled(True)

_progress_cancelled = None
def progress_cancelled(value=None, strict=False):
    global _progress_cancelled
    if value is not None:
        _progress_cancelled = value
    return _progress_cancelled



# This must be absolute, since this script is run directly in Linux.
from sgactions.dispatch import dispatch as _dispatch


if __name__ == '__main__':
    main()
