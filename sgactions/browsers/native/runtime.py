import re

from .core import _capabilities, current_session, send as _send, send_and_recv as _send_and_recv


def is_native():
    return bool(current_session(False))


def alert(message, title=None, strict=False):
    session = current_session(strict)
    if session:
        _send(dst=session['src'], type='alert', title=title, message=message)


def progress(message, title=None, strict=False):
    if title is not None:
        warn('sgactions.browsers.chrome_native.progress title is deprecated')
    session = current_session(strict)
    if session:
        _send(dst=session['src'], type='progress', message=message)
    elif strict:
        raise RuntimeError('no current native handler')


def notify(message, details=None, strict=False):
    session = current_session(strict)
    if session:
        _send(dst=session['src'], type='notify', message=message, details=details)
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

    reply = _send_and_recv(type='confirm', message=message, title=title)
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

    reply = _send_and_recv(
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
