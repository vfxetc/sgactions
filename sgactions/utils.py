from subprocess import call
import sys


def notify(message, title=None, sticky=False):
    
    if title is None:
        title = 'SGActions'

    print '=' * len(str(title))
    print str(title)
    print '=' * len(str(title))
    print message
    print '---'
    
    if sys.platform.startswith('darwin'):
        argv = ['growlnotify',
            '--name', 'Shotgun Action Dispatcher',
            '--title', title,
            '--message', message
        ]
        if sticky:
            argv.append('-s')
    else:
        argv = ['notify-send']
        if sticky:
            argv.extend(['-t', '3600000'])
        argv.extend([title, message])
    call(argv)
