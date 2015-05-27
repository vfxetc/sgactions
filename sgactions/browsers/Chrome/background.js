console.log('Started SGActions background');


var nativePort = chrome.runtime.connectNative('com.keypics.sgactions');

nativePort.onMessage.addListener(function(msg) {
    // console.log("native message:", msg);
    if (msg.dst && msg.dst.tab) {
        var tab = msg.dst.tab;
        msg.dst = msg.dst.next;
        var conn = connections[tab];
        if (conn != undefined) {
            conn.postMessage(msg);
        } else {
            console.log('connection to tab', tab, 'is closed')
        }
    }
});

nativePort.onDisconnect.addListener(function() {
    console.log("native disconnected");
});


var connections = {}

chrome.runtime.onConnect.addListener(function (conn) {

    // console.log("connection", conn);

    connections[conn.sender.tab.id] = conn;

    conn.onDisconnect.addListener(function() {
        connections[conn.sender.tab.id] = undefined;
    })

    conn.onMessage.addListener(function (msg) {
        // console.log('message:', msg);
        if (msg.dst == 'native') {
            msg.src = {
                tab: conn.sender.tab.id,
                next: msg.src
            }
            nativePort.postMessage(msg)
        }
    })

})
