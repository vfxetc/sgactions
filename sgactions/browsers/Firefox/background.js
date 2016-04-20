const { PageMod } = require("sdk/page-mod")
const { OS } = require("sdk/system/runtime")
const { emit } = require('sdk/event/core')
const { spawn } = require("sdk/system/child_process")
const { env } = require('sdk/system/environment')
var self = require('sdk/self')

console.error('SGActions index.js')

exports.main = function(options, callbacks) {
    // console.error('SGActions index.js:main')
}

exports.onUnload = function(reason) {
    console.error('unloading due to ' + reason)
    if (proc) {
        proc.kill()
    }
}

var proc = null;
var size = null;
var buffer = '';

var handleInput = function(data) {

    console.error('stdout', data)
    console.error('handleInput size ' + data.length)

    buffer = buffer.length ? buffer + data : data
    console.error('buffer size ' + buffer.length)

    if (size == null) {
        if (buffer.length < 4) {
            return
        }
        size = decodeInt(buffer)
        if (!size || size > (1024 * 1024)) {
            console.error("invalid message size: " + size)
            proc.kill()
            proc = null
            return
        }
        console.error('recv ' + size)
        buffer = buffer.substr(4)
    }

    if (size > buffer.length) {
        return
    }
    else if (size == buffer.length) {
        raw = buffer
        data = ''
        buffer = ''
    } else {
        raw = buffer.substr(0, size)
        data = buffer.substr(size)
        buffer = ''
    }

    console.error('recv raw: ' + raw)
    var msg = JSON.parse(raw)
    console.error('DECODED:')
    console.error(msg)

    if (data.length) {
        handleInput(data)
    }

}


var connectToNative = function() {
    proc = spawn('/home/mikeb-local/dev/sgactions/sgactions/browsers/Chrome/native.sh', [self.id, 'Firefox'], {
        env: env,
        stdio: ['pipe', 'pipe', 2],
    })
    proc.stdout.on('data', handleInput)
    proc.stderr.on('data', function(data) {
        console.error("stderr: " + data)
    })
    proc.on('close', function(code) {
        console.error('child closed with code ' + code)
        proc = null
    })
}

var encodeInt = function(x) {
    var chr = String.fromCharCode;
    return (
        chr(x       & 0xff) +
        chr(x >> 8  & 0xff) +
        chr(x >> 16 & 0xff) +
        chr(x >> 24 & 0xff)
    )
}

var decodeInt = function(x) {
    var ord = function(i) { x.charCodeAt(i) }
    return (
        ord(0) +
        ord(1) << 8 +
        ord(2) << 16 +
        ord(3) << 24
    )
}


var sendToNative = function(msg) {
    if (!proc) {
        connectToNative()
    }
    var encoded = JSON.stringify(msg)
    console.error("sending message to native " + encoded.length)
    emit(proc.stdin, 'data', encodeInt(encoded.length) + encoded)
}


PageMod({
    include: "*.shotgunstudio.com",
    contentScriptFile: "./main.js",
    contentScriptOptions: {
        pageURL: self.data.url('page')
    },
    onAttach: scriptAttached
})

function scriptAttached(worker) {
    console.error('SGA BG scriptAttached')
    worker.port.on('message', function(msg) {
        console.error('SGA bg message:', msg)
        sendToNative(msg)
    })
}
