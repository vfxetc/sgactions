import hashlib
import os
import re
import sys
import traceback
import urlparse

from . import utils


def main(url):
    
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
    
    try:
        
        # Load the module, and dispatch to the function.
        module = __import__(module_name, fromlist=['.'])
        function = getattr(module, function_name)
        function(**query)
    
    except Exception, e:
        
        exc_message = traceback.format_exc().rstrip()
        query_message = '\n'.join('%s = %r' % x for x in sorted(query.iteritems()))
        environ_message = '\n'.join('%s = %r' % x for x in sorted(os.environ.iteritems()))
        print exc_message
        print '---'
        print query_message
        print '---'
        print environ_message
        print '---'
        
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        hasher = hashlib.sha256(str(exc_type))
        for file_name, line_no, func_name, source in traceback.extract_tb(exc_traceback):
            hasher.update('\n' + file_name + ':' + func_name + ':' + (source or ''))
        mini_uuid = hasher.hexdigest()[:8]
        
        try:
            
            import shotgun_api3_registry
            server = 'https://' + query['server_hostname']
            shotgun = shotgun_api3_registry.connect(name='sgactions.dispatch', server=server)
        
            # Decide what project to attach to. This won't work well on anything
            # but ours.
            if query['server_hostname'] == 'keystone.shotgunstudio.com':
                project = dict(type='Project', id=74)
            else:
                project = dict(type='Project', id=query.get('project_id', 1))
        
            # Look for an existing ticket.
            ticket = shotgun.find_one('Ticket', [('title', 'ends_with', '[%s]' % mini_uuid)])
            if ticket:
                print 'Ticket', ticket['id'], 'found'
        
            # Create a new ticket.
            else:
                ticket = shotgun.create('Ticket', dict(
                    title='%s: %s [%s]' % (exc_type.__name__, e, mini_uuid),
                    sg_status_list='rev', # Pending Review.
                    project=project,
                ))
                print 'Ticket', ticket['id'], 'created'
        
            # Create a reply to that ticket with the traceback.
            reply = dict(content=exc_message + '\n\n' + query_message + '\n\n' + environ_message, entity=ticket)
            if 'user_id' in query:
                reply['user'] = dict(type='HumanUser', id=query['user_id'])
            created = shotgun.create('Reply', reply)
            print 'Reply', created['id'], 'created'
        
            utils.notify(
                title='SGAction Error',
                message='%s: %s\nReplied to Ticket %d [%s].' % (exc_type.__name__, e, ticket['id'], mini_uuid),
                sticky=True,
            )
        
        except Exception as e2:
            utils.notify(
                title='SGAction Fatal Error',
                message='Error while handling error:\n%r from %r' % (e2, e),
                sticky=True,
            )
                

if __name__ == '__main__':
    main(sys.argv[1])
    
    
