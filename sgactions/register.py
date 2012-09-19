"""Register the protocol handler on various OSes."""

from subprocess import call, PIPE
import os
import platform


def main():
    
    if platform.system() == 'Darwin':
        print 'Running "lsregister" ...'
        call([
            '/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister',
            '-f',
            os.path.abspath(os.path.join(__file__, '..', '..', 'applescript_handler.app')),
        ])
        print 'Done.'
    
    elif platform.system() == 'Linux':
        call([
            os.path.abspath(os.path.join(__file__, '..', '..', 'register-linux.sh')),
        ])
    
    else:
        print 'We are not setup for protocol handlers on %s' % platform.system()


if __name__ == '__main__':
    main()
