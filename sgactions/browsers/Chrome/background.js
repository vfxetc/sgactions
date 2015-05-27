console.log('[SGActions] background started');


var nativePort = chrome.runtime.connectNative('com.keypics.sgactions');

nativePort.onMessage.addListener(function(msg) {
    // console.log("native message:", msg);
    if (msg.dst && msg.dst.tab_id) {
        var tab_id = msg.dst.tab_id;
        msg.dst = msg.dst.next;
        var conn = pageConnections[tab_id];
        if (conn != undefined) {
            conn.postMessage(msg);
        } else {
            console.log('[SGActions] connection to tab', tab_id, 'is closed')
            delete pageConnections[tab_id];
        }
    }
});

nativePort.onDisconnect.addListener(function() {
    console.log("[SGActions] native disconnected");
    // TODO: Warn others.
    // TODO: Reconnect.
});


var pageConnections = {}

chrome.runtime.onConnect.addListener(function (conn) {

    // Hold onto this connection by tab ID, so that we can route replies
    // back to it.
    pageConnections[conn.sender.tab.id] = conn;

    conn.onDisconnect.addListener(function() {
        delete pageConnections[conn.sender.tab.id];
    })

    conn.onMessage.addListener(function (msg) {
        if (msg.dst == 'native') {
            msg.src = {
                tab_id: conn.sender.tab.id,
                next: msg.src
            }
            nativePort.postMessage(msg)
        }
    })

})
