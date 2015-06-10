import argparse
import os
import re
import sys
import traceback
import urlparse

from metatools.imports import load_entrypoint

from . import utils
from . import tickets


def parse_url(url):

    # Parse the URL into scheme, path, and query.
    m = re.match(r'^(?:(\w+):)?(.*?)(?:/(.*?))?(?:\?(.*))?$', url)
    scheme, netloc, path, query = m.groups()
    query = urlparse.parse_qs(query, keep_blank_values=True) if query else {}
    
    # Parse the values.
    for k, v in query.items():
        if k == 'ids' or k.endswith('_ids'):
            v[:] = [int(x) for x in v[0].split(',')] if v[0] else []
            continue
        if k.endswith('_id'):
            v[:] = [int(x) for x in v]
        if len(v) == 1 and k not in ('cols', 'column_display_names'):
            query[k] = v[0]
    
    # Parse the path into an entrypoint.
    m = re.match(r'^([\w.]+:\w+)$', netloc)
    if not m:
        raise ValueError('entrypoint must be like "package.module:function"; got "%s"' % netloc)
        return 1

    return m.group(1), query


def dispatch(url, reload=False):

    try:
        entrypoint, kwargs = parse_url(url)
        func = load_entrypoint(entrypoint, reload=reload)
        return func(**kwargs)
    
    except Exception, e:
        try:
            ticket_id = tickets.get_ticket_for_exception(*sys.exc_info())
            tickets.reply_to_ticket(ticket_id, [
                ('Exception', sys.exc_info()),
                ('SGAction Kwargs', kwargs),
                ('OS Environment', dict(os.environ)),
            ], user_id=kwargs.get('user_id'))
            utils.notify(
                title='SGAction Error',
                message='%s: %s\nReplied to Ticket %d.' % (type(e).__name__, e, ticket_id),
                sticky=True,
            )
            return e
        except Exception, e2:
            utils.notify(
                title='SGAction Fatal Error',
                message='Error while handling error:\n%r from %r\n---\n%s' % (e2, e, traceback.format_exc()),
                sticky=True,
            )
            return e2


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', choices=['sgactions.dispatch']) # Just to ignore this parameter.
    parser.add_argument('--chrome-native', action='store_true') # Fall into the native dispatcher.
    parser.add_argument('-f', '--file', action='store_true') # Load the URL from a file.
    parser.add_argument('url', nargs='?', default='')
    args = parser.parse_args()

    if args.chrome_native:
        from sgactions.browsers.chrome_native import main as native_main
        native_main()
        exit()

    url = args.url
    if args.file:
        url = open(args.file).read()
        os.unlink(args.file)

                

if __name__ == '__main__':
    exit(main() or 0)

    
