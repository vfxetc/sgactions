import sys
import re
import urlparse
import os


def main(url):
    
    # Parse the URL into scheme, path, and query.
    m = re.match(r'^(?:(\w+):)?(.*?)(?:\?(.*))?$', url)
    scheme, path, query = m.groups()
    query = urlparse.parse_qs(query, keep_blank_values=True) if query else {}
    
    # Parse the path into an entrypoint.
    m = re.match(r'^([\w.]+)(?::(\w+))?$', path)
    if not m:
        print >>sys.stderr, 'entrypoint must be like "package.module:function"'
        exit(1)
    module_name, function_name = m.groups()
    
    # Load the module, and dispatch to the function.
    module = __import__(module_name, fromlist=['.'])
    if function_name:
        function = getattr(module, function_name)
        function(**query)


def test_kwargs(**kwargs):
    for k, v in sorted(kwargs.iteritems()):
        print '%s = %r' % (k, v)


def test_environ(**kwargs):
    for k, v in sorted(os.environ.iteritems()):
        print '%s = %r' % (k, v)


if __name__ == '__main__':
    main(sys.argv[1])
    
    
