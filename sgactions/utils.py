from subprocess import call
import platform


def notify(message, title="SGActions", sticky=False):
    print message
    if platform.system() == 'Darwin':
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
