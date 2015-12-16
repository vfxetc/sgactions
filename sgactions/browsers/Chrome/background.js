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

        if (msg.src == 'native' && msg.type == 'hello') {
            msg.src = 'background'
            msg.dst = 'page'
            broadcast(msg);
        } else {
            // Let others die.
        }

    } else if (msg.dst == 'native') {
        try {
            nativePort.postMessage(msg)
        } catch (e) {

            // This is a bit of an awkward situation, because they have
            // already sent us a message (potentially a dispatch), and we
            // were unable to send it. We could try to connect and try again,
            // or bounce it back to them.
            
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


var onDisconnect = function(e) {

    console.log("[SGActions] native disconnected");

    // Let everyone know it is down.
    broadcast({
        src: 'background',
        dst: 'page',
        type: 'disconnect',
    })

    // Attempt an immediate reconnect.
    connect()

}


var nativePort = null;
var connect = function() {

    nativePort = chrome.runtime.connectNative('com.westernx.sgactions');
    nativePort.onDisconnect.addListener(onDisconnect);
    nativePort.onMessage.addListener(routeMessage);

    // We will forward this to everyone when we get it back so that they
    // know the system is (back) up.
    routeMessage({
        src: 'background',
        dst: 'native',
        type: 'hello',
    })

}
connect()







chrome.runtime.onConnect.addListener(function (conn) {

    var tab_id = conn.sender.tab.id;
    pageConnections[tab_id] = conn;

    conn.onDisconnect.addListener(function() {
        console.log('[SGActions] connection to tab', tab_id, 'closed')
        delete pageConnections[tab_id];
    })

    // Connect this to the router.
    conn.onMessage.addListener(function (msg) {
        msg.src = {
            tab_id: tab_id,
            next: msg.src
        }
        routeMessage(msg)
    })

})
