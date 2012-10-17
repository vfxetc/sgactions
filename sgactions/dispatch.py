import hashlib
import os
import re
import sys
import traceback
import urlparse

from . import utils
from . import tickets

def main(url):
    
    try:
    
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
        m = re.match(r'^([\w.]+):(\w+)$', netloc)
        if not m:
            print >>sys.stderr, 'entrypoint must be like "package.module:function"'
            exit(1)
        module_name, function_name = m.groups()
    
        # Load the module, and dispatch to the function.
        module = __import__(module_name, fromlist=['.'])
        function = getattr(module, function_name)
        function(**query)
    
    except Exception, e:
        try:
            ticket_id = tickets.get_ticket_for_exception(*sys.exc_info())
            reply_id = tickets.reply_to_ticket(ticket_id, [
                ('Exception', sys.exc_info()),
                ('SGAction Kwargs', query),
                ('OS Environment', dict(os.environ)),
            ], user_id=query.get('user_id'))
            utils.notify(
                title='SGAction Error',
                message='%s: %s\nReplied to Ticket %d.' % (type(e).__name__, e, ticket_id),
                sticky=True,
            )
        except Exception, e2:
            utils.notify(
                title='SGAction Fatal Error',
                message='Error while handling error:\n%r from %r\n---\n%s' % (e2, e, traceback.format_exc()),
                sticky=True,
            )
                

if __name__ == '__main__':
    
    # Really long URLs may come from tempfiles.
    if len(sys.argv) == 3 and sys.argv[1] == '-f':
        path = sys.argv[2]
        url = open(path).read()
        os.unlink(path)
    
    else:
        url = sys.argv[1]
    
    main(url)
    
    
