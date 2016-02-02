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

if __name__ == '__main__':
    sys.modules['sgactions.browsers.chrome_native'] = sys.modules['__main__']


def log(*args):
    sys.stderr.write('[SGActions] %s\n' % ' '.join(str(x) for x in args))
    sys.stderr.flush()


_capabilities = {}
_handlers = {}
_threads = weakref.WeakValueDictionary()
_local = threading.local()


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
        bootstrapper=os.environ.get('SGACTIONS_NATIVE_SH'),
        extension=os.environ.get('SGACTIONS_EXT_ID'),
    )




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

    # We need to take over both stdout and stderr so that print statements
    # don't result in chrome thinking it is getting a message back.
    sys.stdout = sys.stderr = open('/tmp/sgactions.native.log', 'a')

    dispatch_counter = 0

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

        if len(_threads):
            log('%d sessions open' % len(_threads))

        log('recv', size, raw_msg)

        if msg.get('type') not in _handlers:
            reply(msg, type='error', error='unknown message type %r' % msg.get('type'))
            log('unknown message type: %s' % msg.get('type'))

        dispatch_counter += 1

        thread = _threads[dispatch_counter] = threading.Thread(target=_main_thread, args=[msg])
        thread.daemon = True
        thread.session = {
            'type': msg['type'],
            'src': msg.get('src'),
            'token': dispatch_counter,
        }
        thread.start()
        del thread # Kill this reference immediately.



    _running = False


def current_session(strict=True):
    try:
        return threading.current_thread().session
    except AttributeError:
        if strict:
            raise RuntimeError('no current native handler')

def _main_thread(msg):
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


# For runtime!

def is_native():
    return bool(current_session(False))

def alert(message, title=None, strict=False):
    session = current_session(strict)
    if session:
        send(dst=session['src'], type='alert', title=title, message=message)

def progress(message, title=None, strict=False):
    if title is not None:
        warn('sgactions.browsers.chrome_native.progress title is deprecated')
    session = current_session(strict)
    if session:
        send(dst=session['src'], type='progress', message=message)
    elif strict:
        raise RuntimeError('no current native handler')

def notify(message, details=None, strict=False):
    session = current_session(strict)
    if session:
        send(dst=session['src'], type='notify', message=message, details=details)
    elif strict:
        raise RuntimeError('no current native handler')

def confirm(message, title=None, default=None):

    session = current_session(strict=False)
    if not session:
        if default is not None:
            return default
        raise RuntimeError('no current native handler')
    if not _capabilities.get('confirm'):
        if default is not None:
            return default
        raise RuntimeError('confirm is not supported by native handler')

    reply = send_and_recv(type='confirm', message=message, title=title)
    return reply['value']


def select(options, prologue=None, epilogue=None, title=None, default=None):

    session = current_session(strict=False)
    if not session:
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

    reply = send_and_recv(
        type='select',
        title=title,
        prologue=prologue,
        options=options,
        epilogue=epilogue,
    )
    value = reply['value']
    if value is None:
        return default
    return value


# This must be absolute, since this script is run directly in Linux.
from sgactions.dispatch import dispatch as _dispatch


if __name__ == '__main__':
    main()
