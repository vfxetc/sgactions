"""Register the protocol handler on various OSes."""

from subprocess import call, PIPE
import platform
import os


def main():
    
    if platform.system() == 'Darwin':
        call([
            '/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister',
            '-f',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'applescript_handler.app'),
        ])
    
    else:
        print 'We are not setup for procotol handlers on %s' % platform.system()


if __name__ == '__main__':
    main()
