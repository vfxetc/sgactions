"""
This is the MIT license. This software may also be distributed under the same 
terms as Python (the PSF license).

Copyright (c) 2004 Bob Ippolito.

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do 
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.


sys.argv emulation

This module starts a basic event loop to collect file- and url-open AppleEvents. Those get
converted to strings and stuffed into sys.argv. When that is done we continue starting 
the application.

This is a workaround to convert scripts that expect filenames on the command-line to work 
in a GUI environment. GUI applications should not use this feature.

NOTE: This module uses ctypes and not the Carbon modules in the stdlib because the latter
don't work in 64-bit mode and are also not available with python 3.x.
"""

import sys
import os
import time

if sys.version_info[0] == 3:
    def B(value):
        return value.encode('ascii')
else:
    def B(value):
        return value

import ctypes
import struct

class AEDesc (ctypes.Structure):
    _fields_ = [
        ('descKey', ctypes.c_int),
        ('descContent', ctypes.c_void_p),
    ]

class EventTypeSpec (ctypes.Structure):
    _fields_ = [
        ('eventClass',      ctypes.c_int),
        ('eventKind',       ctypes.c_uint),
    ]

def _ctypes_setup():
    carbon = ctypes.CDLL('/System/Library/Carbon.framework/Carbon')

    timer_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_long)

    ae_callback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, 
        ctypes.c_void_p, ctypes.c_void_p)
    carbon.AEInstallEventHandler.argtypes = [ 
            ctypes.c_int, ctypes.c_int, ae_callback,
            ctypes.c_void_p, ctypes.c_char ]
    carbon.AERemoveEventHandler.argtypes = [ 
            ctypes.c_int, ctypes.c_int, ae_callback,
            ctypes.c_char ]

    carbon.AEProcessEvent.restype = ctypes.c_int
    carbon.AEProcessEvent.argtypes = [ctypes.c_void_p]


    carbon.ReceiveNextEvent.restype = ctypes.c_int
    carbon.ReceiveNextEvent.argtypes = [ 
        ctypes.c_long,  ctypes.POINTER(EventTypeSpec),
        ctypes.c_double, ctypes.c_char,
        ctypes.POINTER(ctypes.c_void_p)
    ]

    
    carbon.AEGetParamDesc.restype = ctypes.c_int
    carbon.AEGetParamDesc.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(AEDesc)]

    carbon.AECountItems.restype = ctypes.c_int
    carbon.AECountItems.argtypes = [ ctypes.POINTER(AEDesc),
            ctypes.POINTER(ctypes.c_long) ]

    carbon.AEGetNthDesc.restype = ctypes.c_int
    carbon.AEGetNthDesc.argtypes = [ 
            ctypes.c_void_p, ctypes.c_long, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_void_p ]

    carbon.AEGetDescDataSize.restype = ctypes.c_int
    carbon.AEGetDescDataSize.argtypes = [ ctypes.POINTER(AEDesc) ]

    carbon.AEGetDescData.restype = ctypes.c_int
    carbon.AEGetDescData.argtypes = [ 
            ctypes.POINTER(AEDesc),
            ctypes.c_void_p,
            ctypes.c_int,
            ]


    carbon.FSRefMakePath.restype = ctypes.c_int
    carbon.FSRefMakePath.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]

    return carbon

def _run_argvemulator(timeout = 60):

    # Configure ctypes
    carbon = _ctypes_setup()

    # Is the emulator running?
    running = [True]

    # Configure AppleEvent handlers
    ae_callback = carbon.AEInstallEventHandler.argtypes[2]

    kAEInternetSuite,   = struct.unpack('>i', B('GURL'))
    kAEISGetURL,        = struct.unpack('>i', B('GURL'))
    kCoreEventClass,    = struct.unpack('>i', B('aevt'))
    kAEOpenApplication, = struct.unpack('>i', B('oapp'))
    kAEOpenDocuments,   = struct.unpack('>i', B('odoc'))
    keyDirectObject,    = struct.unpack('>i', B('----'))
    typeAEList,         = struct.unpack('>i', B('list'))
    typeChar,           = struct.unpack('>i', B('TEXT'))
    typeFSRef,          = struct.unpack('>i', B('fsrf'))
    FALSE               = B('\0')
    TRUE               = B('\1')

    kEventClassAppleEvent, = struct.unpack('>i', B('eppc'))
    kEventAppleEvent = 1


    @ae_callback
    def open_app_handler(message, reply, refcon):
        running[0] = False
	return 0

    carbon.AEInstallEventHandler(kCoreEventClass, kAEOpenApplication,
            open_app_handler, 0, FALSE)

    @ae_callback
    def open_file_handler(message, reply, refcon):
        listdesc = AEDesc()
        sts = carbon.AEGetParamDesc(message, keyDirectObject, typeAEList,
                ctypes.byref(listdesc))
        if sts != 0:
            print >>sys.stderr, "argvemulator warning: cannot unpack open document event"
            running[0] = False
            return

        item_count = ctypes.c_long()
        sts = carbon.AECountItems(ctypes.byref(listdesc), ctypes.byref(item_count))
        if sts != 0:
            print >>sys.stderr, "argvemulator warning: cannot unpack open document event"
            running[0] = False
            return

        desc = AEDesc()
        for i in range(item_count.value):
            sts = carbon.AEGetNthDesc(ctypes.byref(listdesc), i+1, typeFSRef, 0, ctypes.byref(desc))
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot unpack open document event"
                running[0] = False
                return

            sz = carbon.AEGetDescDataSize(ctypes.byref(desc))
            buf = ctypes.create_string_buffer(sz)
            sts = carbon.AEGetDescData(ctypes.byref(desc), buf, sz)
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot extract open document event"
                continue

            fsref = buf

            buf = ctypes.create_string_buffer(1024)
            sts = carbon.FSRefMakePath(ctypes.byref(fsref), buf, 1023)
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot extract open document event"
                continue

            print >>sys.stderr, "Adding: %s"%(repr(buf.value.decode('utf-8')),)

            if sys.version_info[0] > 2:
                sys.argv.append(buf.value.decode('utf-8'))
            else:
                sys.argv.append(buf.value)

        running[0] = False
	return 0

    carbon.AEInstallEventHandler(kCoreEventClass, kAEOpenDocuments,
            open_file_handler, 0, FALSE)

    @ae_callback
    def open_url_handler(message, reply, refcon):
        listdesc = AEDesc()
        ok = carbon.AEGetParamDesc(message, keyDirectObject, typeAEList,
                ctypes.byref(listdesc))
        if ok != 0:
            print >>sys.stderr, "argvemulator warning: cannot unpack open document event"
            running[0] = False
            return

        item_count = ctypes.c_long()
        sts = carbon.AECountItems(ctypes.byref(listdesc), ctypes.byref(item_count))
        if sts != 0:
            print >>sys.stderr, "argvemulator warning: cannot unpack open url event"
            running[0] = False
            return

        desc = AEDesc()
        for i in range(item_count.value):
            sts = carbon.AEGetNthDesc(ctypes.byref(listdesc), i+1, typeChar, 0, ctypes.byref(desc))
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot unpack open URL event"
                running[0] = False
                return

            sz = carbon.AEGetDescDataSize(ctypes.byref(desc))
            buf = ctypes.create_string_buffer(sz)
            sts = carbon.AEGetDescData(ctypes.byref(desc), buf, sz)
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot extract open URL event"

            else:
                if sys.version_info[0] > 2:
                    sys.argv.append(buf.value.decode('utf-8'))
                else:
                    sys.argv.append(buf.value)

        running[0] = False
	return 0
    
    carbon.AEInstallEventHandler(kAEInternetSuite, kAEISGetURL,
            open_url_handler, 0, FALSE)

    # Remove the funny -psn_xxx_xxx argument
    if len(sys.argv) > 1 and sys.argv[1][:4] == '-psn':
	del sys.argv[1]

    start = time.time()
    now = time.time()
    eventType = EventTypeSpec()
    eventType.eventClass = kEventClassAppleEvent
    eventType.eventKind = kEventAppleEvent

    while running[0] and now - start < timeout:
        event = ctypes.c_void_p()

        sts = carbon.ReceiveNextEvent(1, ctypes.byref(eventType), 
                start + timeout - now, TRUE, ctypes.byref(event))
        if sts != 0:
            print >>sys.stderr, "argvemulator warning: fetching events failed"
            break

        sts = carbon.AEProcessEvent(event)
        if sts != 0:
            print >>sys.stderr, "argvemulator warning: processing events failed"
            break
        

    carbon.AERemoveEventHandler(kCoreEventClass, kAEOpenApplication, 
            open_app_handler, FALSE)
    carbon.AERemoveEventHandler(kCoreEventClass, kAEOpenDocuments,
            open_file_handler, FALSE)
    carbon.AERemoveEventHandler(kAEInternetSuite, kAEISGetURL,
            open_url_handler, FALSE)

def _argv_emulation():
    import sys
    # only use if started by LaunchServices
    for arg in sys.argv[1:]:
        if arg.startswith('-psn'):
            _run_argvemulator()
            break
_argv_emulation()