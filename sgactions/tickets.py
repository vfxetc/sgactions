import os
import traceback
import hashlib
import sys


def ticket_exception(args=None, kwargs=None, include_environ=True):
    
    parts = []
    parts.append(('Traceback', traceback.format_exc().rstrip()))
    if args is not None:
        parts.append(('Args', '\n'.join(repr(x) for x in args)))
    if kwargs is not None:
        parts.append(('Kwargs', '\n'.join('%s = %r' % x for x in sorted(kwargs.iteritems()))))
    if include_environ:
        parts.append(('Environ', '\n'.join('%s = %r' % x for x in sorted(os.environ.iteritems()))))
    
    for name, content in parts:
        print name
        print '=' * len(name)
        print content
        print '---'
    
    # Calculate the hash for Ticket lookup.
    exc_type, exc_value, exc_traceback = sys.exc_info()
    hasher = hashlib.sha256(str(exc_type))
    for file_name, line_no, func_name, source in traceback.extract_tb(exc_traceback):
        hasher.update('\n' + file_name + ':' + func_name + ':' + (source or ''))
    mini_uuid = hasher.hexdigest()[:8]
    
    # Get the Shotgun and Project.
    # TODO: Somehow pass this in later.
    import shotgun_api3_registry
    shotgun = shotgun_api3_registry.connect(name='sgactions.dispatch')
    project = dict(type='Project', id=74)
    
    # Look for an existing ticket, or create a new one.
    ticket = shotgun.find_one('Ticket', [('title', 'ends_with', '[%s]' % mini_uuid)])
    if ticket is None:
        ticket = shotgun.create('Ticket', dict(
            title='%s: %s [%s]' % (exc_type.__name__, exc_value, mini_uuid),
            sg_status_list='rev', # Pending Review.
            project=project,
        ))
    
    # Create a reply to that ticket with the traceback.
    reply = dict(content='\n\n'.join('%s\n%s\n%s' % (name, '='*len(name), content) for name, content in parts), entity=ticket)
    if 'user_id' in kwargs:
        reply['user'] = dict(type='HumanUser', id=kwargs['user_id'])
    created = shotgun.create('Reply', reply)
        
    return mini_uuid, ticket['id'], created['id']
    
    