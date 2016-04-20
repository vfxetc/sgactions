import argparse
import os
import re
import sys
import traceback
import urlparse

# HACK: Just for Mark Media for today.
sys.path.append('/home/mikeb-local/dev/metatools')

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
        kwargs = {}
        entrypoint, kwargs = parse_url(url)
        func = load_entrypoint(entrypoint, reload=reload)
        return func(**kwargs)

    except Exception, e:

        # Default value in case there is an error in traceback.format_exc()...
        tb = 'ERROR DURING TRACEBACK'

        try:
            tb = traceback.format_exc()

            ticket_id = tickets.get_ticket_for_exception(*sys.exc_info())
            tickets.reply_to_ticket(ticket_id, [
                ('Exception', sys.exc_info()),
                ('SGAction Kwargs', kwargs or url),
                ('OS Environment', dict(os.environ)),
            ], user_id=kwargs.get('user_id'))

            utils.alert(
                title='Unhandled %s' % type(e).__name__,
                message='<pre>%s</pre>\n\nReplied to Ticket %d.' % (tb, ticket_id),
            )

            return e

        except Exception, e2:

            utils.alert(
                title='Fatal Unhandled %s' % type(e2).__name__,
                message='<pre>%s</pre>\n\nDuring handling of the above exception, another exception occurred:\n\n<pre>%s</pre>' % (tb, traceback.format_exc()),
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

    sys.stdout = sys.stderr = open('/tmp/sgactions.native.log', 'a')

    dispatch(url)



if __name__ == '__main__':
    exit(main() or 0)
