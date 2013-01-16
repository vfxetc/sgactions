import hashlib
import os
import traceback
import re
import types
import textwrap


def guess_user_id():
    login = os.getlogin()

    import shotgun_api3_registry
    shotgun = shotgun_api3_registry.connect(name='sgactions.dispatch')
    
    human = shotgun.find_one('HumanUser', [('email', 'starts_with', login + '@')])
    return human and human['id']


def exception_uuid(exc_type, exc_value, exc_traceback):
    """Calculate a 32-bit UUID for a given exception.
    
    Useful for looking for an existing ticket coresponding to a given exception.
    Takes into account the type of exception, and the name of every file and
    function in the traceback, along with the source code from those lines.
    
    This should remain consistant until a file or function is renamed, the
    source changed on the precise lines in the traceback, or the evaluation path
    changes.
    
    :return: Hex ``str`` of length 8.
    
    """
    hasher = hashlib.sha256(str(exc_type))
    for file_name, line_no, func_name, source in traceback.extract_tb(exc_traceback):
        hasher.update('\n' + file_name + ':' + func_name + ':' + (source or ''))
    return hasher.hexdigest()[:8]


def get_ticket_for_exception(exc_type=None, exc_value=None, exc_traceback=None, title=None):
    """Get (or create) a ticket for the given exception.
    
    Uses :func:`exception_uuid` to identify existing tickets by looking for the
    tag in square brackets in the title. E.g. ``Something happened. [deadbeef]``.
    
    :param str title: Title to use if creating a new ticket. Defaults to the
        exception type and value.
    :returns: The ID of the ticket.
    
    """
    if exc_type and exc_value and exc_traceback:
        mini_uuid = exception_uuid(exc_type, exc_value, exc_traceback)
    else:
        mini_uuid = None
        
    # Get the Shotgun and Project.
    # TODO: Somehow pass this in later.
    import shotgun_api3_registry
    shotgun = shotgun_api3_registry.connect(name='sgactions.dispatch')
    project = dict(type='Project', id=74)
    
    # Look for an existing ticket, or create a new one.
    if mini_uuid:
        ticket = shotgun.find_one('Ticket', [('title', 'contains', '[%s]' % mini_uuid)])
    else:
        ticket = None
    if ticket is None:
        
        if title is None:
            if exc_type and exc_value:
                title = '%s: %s' % (exc_type.__name__, exc_value)
            else:
                title = 'New Ticket'

        uuid_tag = ' [%s]' % mini_uuid if mini_uuid else ''

        # Automatically truncate to 255 escaped chars. Remember that the uuid
        # tag will consume 11, and another 3 for ellipsis, and a guess as to
        # how many due to the string escaping.
        if len(title.encode('string-escape')) + len(uuid_tag) > 255:
            title = title[:
                255
                - (len(title.encode('string-escape')) - len(title))
                - len(uuid_tag)
                - 3
            ] + '...'
        title = '%s%s' % (title, uuid_tag)

        ticket = shotgun.create('Ticket', dict(
            title=title,
            sg_status_list='rev', # Pending Review.
            project=project,
        ))
    
    return ticket['id']
    

def reply_to_ticket(ticket_id, content, user_id=None):
    """Create a structured reply to a ticket.
    
    :param int ticket_id: The ticket to reply to.
    :param content: ``str``, ``dict``, or iterator of ``(title, content``) pairs.
    :returns: ``(reply_id, reply_content)``.
    
    """
    
    if isinstance(content, dict):
        content = sorted(content.iteritems())

    if not isinstance(content, basestring):
        parts = []
        for heading, part in content:
            
            # Mappings.
            if isinstance(part, dict):
                parts.append((heading, '\n'.join('%s = %r' % x
                    for x in sorted(part.iteritems())
                )))
            
            # Iterators.
            elif isinstance(part, (list, tuple)):
                
                # Exceptions.
                if (len(part) == 3 and
                    issubclass(part[0], Exception) and
                    isinstance(part[1], Exception) and
                    isinstance(part[2], types.TracebackType)
                ):
                    parts.append((heading, '\n'.join(traceback.format_exception(*part)).rstrip()))
                
                # Iterators.
                else:
                    parts.append((heading, '\n'.join('- %r' % x for x in part)))
            
            # The rest.
            else:
                parts.append((heading, str(part)))
        
        # Join the parts.
        content = '\n\n'.join('%s\n%s\n%s' % (heading, '=' * len(heading), part) for heading, part in parts)

        # Line wrap (each line seperately).
        line_width = 100
        content = '\n'.join(textwrap.fill(line, line_width, break_long_words=False, replace_whitespace=False) for line in content.splitlines())

        # Break up long words.
        def break_long(m):
            word = m.group(1)
            return '\\\n'.join(word[i:i+line_width] for i in xrange(0, len(word), line_width))
        content = re.sub(r'(\S{%d,})' % line_width, break_long, content)

        # Don't mark it up.
        content = 'bc..\n' + content
    
    # Create a reply to that ticket with the traceback.
    reply = dict(content=content, entity=dict(type='Ticket', id=ticket_id))
    if user_id:
        reply['user'] = dict(type='HumanUser', id=user_id)
    
    # Get the Shotgun and Project.
    # TODO: Somehow pass this in later.
    import shotgun_api3_registry
    shotgun = shotgun_api3_registry.connect(name='sgactions.dispatch')
    
    created = shotgun.create('Reply', reply)
    return created['id'], content


def attach_to_ticket(ticket_id, attachment):
    """Attach a file to a ticket."""
    import shotgun_api3_registry
    shotgun = shotgun_api3_registry.connect(name='sgactions.dispatch')
    shotgun.upload('Ticket', ticket_id, attachment, 'attachments')
