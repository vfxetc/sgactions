import datetime
import hashlib
import os
import re
import sys
import tempfile
import textwrap
import traceback
import types

import siteconfig

from .utils import get_shotgun


def guess_user_id():
    login = os.getlogin()
    sg = get_shotgun()
    human = sg.find_one('HumanUser', [('email', 'starts_with', login + '@')])
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
        
    # Get the Shotgun.
    shotgun = get_shotgun()
    
    # Look for an existing ticket, or create a new one.
    if mini_uuid:
        ticket = shotgun.find_one('Ticket', [('title', 'contains', '[%s]' % mini_uuid)])
        if ticket:
            return ticket['id']

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

    # Lookup where we are storing this ticket.
    project_id = siteconfig.get('SGACTIONS_TICKET_PROJECT')
    if not project_id:
        raise ValueError('SGACTIONS_TICKET_PROJECT must be set via siteconfig')
    tool_id = siteconfig.get('SGACTIONS_TICKET_TOOL')

    ticket = shotgun.create('Ticket', dict(
        title=title,
        sg_status_list='rev', # Pending Review.
        project={'type': 'Project', 'id': project_id},
        sg_tool={'type': 'Tool', 'id': tool_id} if tool_id else None,
    ))
    
    return ticket['id']
    

def reply_to_ticket(ticket_id, content, user_id=None):
    """Create a structured reply to a ticket.
    
    :param int ticket_id: The ticket to reply to.
    :param content: ``str``, ``dict``, or iterator of ``(title, content``) pairs.
    :returns: ``(reply_id, reply_content)``.
    
    """
    
    user_comment = None
    exc_type = None

    if isinstance(content, dict):
        content = sorted(content.iteritems())

    if not isinstance(content, basestring):
        parts = []
        for heading, part in content:
            
            # This one gets special cased into a Reply.
            if heading.lower() == 'user comment':
                user_comment = part

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
                    exc_type = part[0]
                    parts.append((heading, '\n'.join(traceback.format_exception(*part)).rstrip()))
                
                # Iterators.
                else:
                    parts.append((heading, '\n'.join('- %r' % x for x in part)))
            
            # The rest.
            else:
                parts.append((heading, str(part)))
        
        # Join the parts.
        content = '\n\n'.join('%s\n%s\n%s' % (heading, '=' * len(heading), part) for heading, part in parts)
    
    # Get the Shotgun and Project.
    # TODO: Somehow pass this in later.
    shotgun = get_shotgun()

    # Convert requested user ID to a login.
    if user_id:
        user = shotgun.find_one('HumanUser', [('id', 'is', user_id)], ['login'])
        if user:
            shotgun.config.sudo_as_login = user['login']

    # Make sure we do have a login.
    if not shotgun.config.sudo_as_login:
        user = shotgun.find_one('HumanUser', [('email', 'starts_with', os.getlogin() + '@')], ['login'])
        if user:
            shotgun.config.sudo_as_login = user['login']
    
    reply = None

    if user_comment:
        reply = shotgun.create('Reply', {
            'content': user_comment,
            'entity': {'type': 'Ticket', 'id': ticket_id},
        })

    if content.strip():
        with tempfile.NamedTemporaryFile(suffix='ticket-%d-reply.txt' % ticket_id) as fh:
            fh.write(content)
            fh.flush()
            shotgun.upload('Ticket', ticket_id, fh.name, 'attachments',
               display_name='Ticket-%d.%s.%s.txt' % (
                    ticket_id,
                    exc_type.__name__ if exc_type else 'details',
                    datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                ),
            )

    return reply and reply['id'], content


def attach_to_ticket(ticket_id, attachment):
    """Attach a file to a ticket."""
    shotgun = get_shotgun()
    shotgun.upload('Ticket', ticket_id, attachment, 'attachments')


if __name__ == '__main__':

    try:
        raise ValueError('this is a test')
    except:
        ticket_id = get_ticket_for_exception(*sys.exc_info(), title='Testing Ticket Submittion')
        print 'Ticket ID', ticket_id
        reply_id, _ = reply_to_ticket(ticket_id, {
            'User Comment': 'This is just a test',
            'Exception': sys.exc_info(),
        })
        print 'Reply ID', reply_id
