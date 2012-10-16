import hashlib
import os
import sys
import textwrap
import traceback

def exception_hash(exc_type, exc_value, exc_traceback):
    hasher = hashlib.sha256(str(exc_type))
    for file_name, line_no, func_name, source in traceback.extract_tb(exc_traceback):
        hasher.update('\n' + file_name + ':' + func_name + ':' + (source or ''))
    return hasher.hexdigest()[:8]

def create_ticket(exc_type=None, exc_value=None, exc_traceback=None, args=None,
    kwargs=None, include_environ=True, title=None, description=None,
    attachments=[]):
    
    parts = []
    if description and description.strip():
        parts.append(('Description', description.strip()))
    if exc_type and exc_value and exc_traceback:
        parts.append(('Traceback', '\n'.join(traceback.format_exception(exc_type, exc_value, exc_traceback)).rstrip()))
    if args is not None:
        parts.append(('Args', '\n'.join(repr(x) for x in args)))
    if kwargs is not None:
        parts.append(('Kwargs', '\n'.join('%s = %r' % x for x in sorted(kwargs.iteritems()))))
    if include_environ:
        blob = '\n'.join(
            textwrap.fill('%s = %r' % x, 80)
            for x in sorted(os.environ.iteritems())
        )
        parts.append(('Environ', blob))
    
    for name, content in parts:
        print name
        print '=' * len(name)
        print content
        print '---'
    
    # Calculate the hash for Ticket lookup.
    if exc_type and exc_value and exc_traceback:
        mini_uuid = exception_hash(exc_type, exc_value, exc_traceback)
    else:
        mini_uuid = None
    
    # Get the Shotgun and Project.
    # TODO: Somehow pass this in later.
    import shotgun_api3_registry
    shotgun = shotgun_api3_registry.connect(name='sgactions.dispatch')
    project = dict(type='Project', id=74)
    
    # Look for an existing ticket, or create a new one.
    if mini_uuid:
        ticket = shotgun.find_one('Ticket', [('title', 'ends_with', '[%s]' % mini_uuid)])
    else:
        ticket = None
    if ticket is None:
        if title is None:
            title = '%s: %s' % (exc_type.__name__, exc_value)
        uuid_tag = ' [%s]' % mini_uuid if mini_uuid else ''
        ticket = shotgun.create('Ticket', dict(
            title='%s%s' % (title, uuid_tag),
            sg_status_list='rev', # Pending Review.
            project=project,
        ))
    
    # Create a reply to that ticket with the traceback.
    reply = dict(content='\n\n'.join('%s\n%s\n%s' % (name, '='*len(name), content) for name, content in parts), entity=ticket)
    if kwargs and 'user_id' in kwargs:
        reply['user'] = dict(type='HumanUser', id=kwargs['user_id'])
    created = shotgun.create('Reply', reply)
    
    for attachment in attachments:
        if not attachment:
            continue
        shotgun.upload('Ticket', ticket['id'], attachment, 'attachments')
            
    return mini_uuid, ticket['id'], created['id']
    
    