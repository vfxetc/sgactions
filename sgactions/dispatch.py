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
    
    kwargs = urlparse.parse_qs(query, keep_blank_values=True) if query else {}
    for k, v in kwargs.iteritems():
        if len(v) == 1 and k not in ('cols', 'column_display_names'):
            kwargs[k] = v = v[0]
        if k.endswith('_id') and v.isdigit():
            kwargs[k] = int(v)

    # Parse the path into an entrypoint.
    m = re.match(r'^([\w.]+:\w+)$', netloc)
    if not m:
        raise ValueError('entrypoint must be like "package.module:function"; got "%s"' % netloc)
        return 1

    return m.group(1), kwargs


def parse_raw_kwargs(kwargs):
    for k, v in kwargs.items():
        if not isinstance(k, basestring):
            continue

        # From a URL, these are always strings.
        # Via the web-ext, they are sometimes strings. It depends on the
        # internal javascript, which makes the assumption that it will all
        # get turned into strings to make it to the backend.

        if k == 'ids' or k.endswith('_ids'):
            if isinstance(v, basestring):
                kwargs[k] = [int(x) for x in v.split(',')] if v else []
            elif isinstance(v, int):
                kwargs[k] = [v]

        if k == 'id' or k.endswith('id'):
            if isinstance(v, basestring) and v.isdigit():
                kwargs[k] = int(v)


def dispatch(entrypoint=None, kwargs=None, url=None, reload=False):

    try:

        if (entrypoint and url) or not (entrypoint or url):
            raise ValueError("Need one of entrypoint or URL.")

        if entrypoint and kwargs is None:
            raise ValueError("Need kwargs with entrypoint.")
        if url:
            entrypoint, kwargs = parse_url(url)

        parse_raw_kwargs(kwargs)

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

    dispatch(url=url)



if __name__ == '__main__':
    exit(main() or 0)
