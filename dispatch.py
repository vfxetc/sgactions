import sys
import re
import urlparse
import os


def main(url):
    
    # Parse the URL into scheme, path, and query.
    m = re.match(r'^(?:(\w+):)?(.*?)(?:\?(.*))?$', url)
    scheme, path, query = m.groups()
    query = urlparse.parse_qs(query, keep_blank_values=True) if query else {}
    
    # Parse the values.
    for k, v in query.items():
        if k == 'ids' or k.endswith('_ids'):
            v[:] = [int(x) for x in v[0].split(',')]
            continue
        if k.endswith('_id'):
            v[:] = [int(x) for x in v]
        if len(v) == 1 and k not in ('cols', 'column_display_names'):
            query[k] = v[0]
    
    # Parse the path into an entrypoint.
    m = re.match(r'^([\w.]+):(\w+)$', path)
    if not m:
        print >>sys.stderr, 'entrypoint must be like "package.module:function"'
        exit(1)
    module_name, function_name = m.groups()
    
    # Load the module, and dispatch to the function.
    # TODO: Catch errors, and log them to Shotgun.
    module = __import__(module_name, fromlist=['.'])
    function = getattr(module, function_name)
    function(**query)


if __name__ == '__main__':
    main(sys.argv[1])
    
    
