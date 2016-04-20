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


var proc = spawn('/bin/bash', ['-c', 'echo \'{"key": "value"}\'; echo not JSON'], {
    env: env
})

proc.stdout.on('data', function (data) {
    console.error('SGACtions proc stdout: ' + data)
    var lines = data.match(/[^\r\n]+/g)
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if (line.length) {
            try {
                var loaded = JSON.parse(line)
                console.error(loaded)
            } catch (e) {
                // console.error(e)
            }
        }
    }
})

console.error('SPAWNED PROC')

PageMod({
    include: "*.shotgunstudio.com",
    contentScriptFile: "./main.js",
    contentScriptOptions: {
        styles: [
            self.data.url("page/css/silk/silk-icons.css"),
            self.data.url("page/css/sgactions.css")
        ], scripts: [
            self.data.url("page/ui.js"),
            self.data.url("page/core.js"),
            self.data.url("page/menu.js")
        ]
    }
})
