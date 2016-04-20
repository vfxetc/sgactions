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

var handleInput = function(data) {

    if (!this.buffer) {
        this.buffer = data
    } else {
        this.buffer += data
    }

    while (this.buffer) {
        var parts = this.buffer.match(/^([^\n\r]*)[\n\r]+(.*)$/)
        if (!parts) {
            return
        }
        var raw = parts[1];
        this.buffer = parts[2] || '';

        var msg = JSON.parse(raw)
        console.error('DECODED:')
        console.error(msg)

        // Dispatch it to the worker.
        var id = msg.dst.tab_id;
        var worker = workers[msg.dst.tab_id]
        msg.dst = msg.dst.next
        worker.port.emit('message', msg)

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


var sendToNative = function(msg) {
    if (!proc) {
        connectToNative()
    }
    var encoded = JSON.stringify(msg)
    //console.error("sending message to native " + encoded.length)
    emit(proc.stdin, 'data', encoded + '\n')
}

PageMod({
    include: "*.shotgunstudio.com",
    contentScriptFile: "./main.js",
    contentScriptOptions: {
        pageURL: self.data.url('page')
    },
    onAttach: scriptAttached
})

var workerCount = 0
var workers = {}
function scriptAttached(worker) {
    workerCount += 1
    var id = workerCount
    workers[id] = worker
    //console.error('SGA BG scriptAttached')
    worker.port.on('message', function(msg) {
        //console.error('SGA bg message:', msg)
        // Add routing info.
        msg.src = {tab_id: id, next: msg.src}
        sendToNative(msg)
    })
}
