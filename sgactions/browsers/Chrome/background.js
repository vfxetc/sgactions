console.log('[SGActions] background started');

var nativePort = chrome.runtime.connectNative('com.westernx.sgactions');

nativePort.onMessage.addListener(function(msg) {
    if (msg.dst && msg.dst.tab_id) {
        console.log("[SGActions] message to", msg.dst.tab_id, msg);
        var tab_id = msg.dst.tab_id;
        msg.dst = msg.dst.next;
        var conn = pageConnections[tab_id];
        if (conn != undefined) {
            conn.postMessage(msg);
        } else {
            console.log('[SGActions] connection to tab', tab_id, 'is closed')
            delete pageConnections[tab_id];
        }
    } else {
        console.log("[SGActions] UNHANDLED message from native", msg);
    }
});

nativePort.onDisconnect.addListener(function() {
    console.log("[SGActions] native disconnected");
    broadcast({
        src: 'background',
        dst: 'page'
    })
    // TODO: Warn others.
    // TODO: Reconnect.
});


var pageConnections = {}

var broadcast = function(msg) {
    for (tab in pageConnections) {
        var conn = pageConnections[tab]
        if (conn != undefined) {
            conn.postMessage(msg)
        }
    }
}

chrome.runtime.onConnect.addListener(function (conn) {

    // Hold onto this connection by tab ID, so that we can route replies
    // back to it.
    pageConnections[conn.sender.tab.id] = conn;

    conn.onDisconnect.addListener(function() {
        delete pageConnections[conn.sender.tab.id];
    })

    conn.onMessage.addListener(function (msg) {
        console.log('[SGActions] message from', conn.sender.tab.id, msg)
        if (msg.dst == 'native') {
            msg.src = {
                tab_id: conn.sender.tab.id,
                next: msg.src
            }
            try {
                nativePort.postMessage(msg)
            } catch (e) {
                conn.postMessage({
                    src: 'native',
                    dst: msg.src.next,
                    error: e.toString()
                })
            }
        }
    })

})
