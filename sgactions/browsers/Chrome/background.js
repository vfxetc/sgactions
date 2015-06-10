console.log('[SGActions] background started; runtime ID:', chrome.runtime.id);


var logMessage = function(msg) {
    var dst = msg.dst && msg.dst.tab_id ? msg.dst.tab_id : msg.dst;
    var src = msg.src && msg.src.tab_id ? msg.src.tab_id : msg.src;
    console.log("[SGActions]", src, 'to', dst, msg);
}

var routeMessage = function(msg) {

    var dst = msg.dst && msg.dst.tab_id ? msg.dst.tab_id : msg.dst;
    var src = msg.src && msg.src.tab_id ? msg.src.tab_id : msg.src;
    console.log("[SGActions] message from", src, 'to', dst, msg);

    if (msg.dst == 'background') {
        // let it die here

    } else if (msg.dst == 'native') {
        try {
            nativePort.postMessage(msg)
        } catch (e) {
            console.log("[SGActions] native errored:", e);
            broadcast({
                src: 'background',
                dst: 'page',
                type: 'disconnect',
                error: e.toString()
            })
        }

    } else if (msg.dst && msg.dst.tab_id) {
        var tab_id = msg.dst.tab_id;
        msg.dst = msg.dst.next;
        var conn = pageConnections[tab_id];
        if (conn != undefined) {
            conn.postMessage(msg);
        } else {
            console.log('[SGActions] connection to tab', tab_id, 'is closed?!')
            delete pageConnections[tab_id];
        }

    } else {
        console.log("[SGActions] bad destination:", msg.dst, dst);

    }

}

var pageConnections = {}

var broadcast = function(msg) {
    for (tab in pageConnections) {
        var conn = pageConnections[tab]
        if (conn != undefined) {
            conn.postMessage(msg)
        }
    }
}


var nativePort = chrome.runtime.connectNative('com.westernx.sgactions');

nativePort.onDisconnect.addListener(function(e) {
    console.log("[SGActions] native disconnected", e);
    broadcast({
        src: 'background',
        dst: 'page',
        type: 'disconnect',
    })
    // TODO: reconnect
});

nativePort.onMessage.addListener(routeMessage)


// We are all done setting up our connection to the native; say hello!
routeMessage({
    src: 'background',
    dst: 'native',
    type: 'hello',
})



chrome.runtime.onConnect.addListener(function (conn) {

    var tab_id = conn.sender.tab.id;
    pageConnections[tab_id] = conn;

    conn.onDisconnect.addListener(function() {
        console.log('[SGActions] connection to tab', tab_id, 'closed')
        delete pageConnections[tab_id];
    })

    conn.onMessage.addListener(function (msg) {
        msg.src = {
            tab_id: tab_id,
            next: msg.src
        }
        routeMessage(msg)
    })

})
