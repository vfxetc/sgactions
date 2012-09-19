"""Register the protocol handler on various OSes."""

from subprocess import call, Popen, PIPE
import os
import platform
import re

def main():
    
    if platform.system() == 'Darwin':
        lsregister = '/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister'
        handler = os.path.abspath(os.path.join(__file__, '..', '..', 'Shotgun Action Dispatcher.app'))
        print 'Cleaning old handlers...'
        proc = Popen([lsregister, '-dump'], stdout=PIPE, stderr=PIPE)
        for line in proc.stdout:
            m = re.match(r'\s*path:\s*(.+?/sgactions/.+?\.app)\s*$', line)
            if m and m.group(1) != handler:
                print m.group(1)
                call([lsregister, '-u', m.group(1)], stdout=PIPE, stderr=PIPE)
        print 'Registering new handler...'
        call([
            lsregister,
            '-v',
            handler,
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
