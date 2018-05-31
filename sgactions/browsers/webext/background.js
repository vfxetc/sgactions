console.log('[SGActions] Background started; runtime ID:', chrome.runtime.id);


var connectDelay = 0;

var pageConnections = {}

var broadcast = function(msg) {
    for (tab in pageConnections) {
        var conn = pageConnections[tab]
        if (conn != undefined) {
            conn.postMessage(msg)
        }
    }
}



var onDisconnect = function(thisId) {

    console.log("[SGActions] Native #" + thisId + " disconnected.");

    // Let everyone know it is down.
    broadcast({
        src: 'background',
        dst: 'page',
        type: 'disconnect',
    })

    if (thisId == lastNativeId) {
        // Attempt an immediate reconnect.
        console.log("[SGActions] Reconnecting in " + connectDelay + "ms...")
        setTimeout(connect, connectDelay);
        connectDelay = Math.min(5000, connectDelay * 2 || 100);
    } else {
        console.log("[SGActions] skipping automatic reconnect as", thisId, '!=', lastNativeId)
    }

}


var nativePort = null;
var lastNativeId = 0;

var connect = function() {

    var thisId = lastNativeId + 1
    lastNativeId = thisId

    console.log('[SGActions] starting native connection', thisId);

    nativePort = chrome.runtime.connectNative('com.vfxetc.sgactions');
    nativePort.onDisconnect.addListener(onDisconnect.bind(nativePort, thisId));
    nativePort.onMessage.addListener(routeMessage);

    // Let everyone know it is back up.
    broadcast({
        src: 'background',
        dst: 'page',
        type: 'connect',
    })

}



var routeMessage = function(msg) {

    if (!msg.dst || !msg.src || !msg.type) {
        console.log("[SGActions/background] Message is malformed:", msg);
        return;
    }

    if (msg.src == 'native') {
        // Our connection is good, so next time try immediately.
        connectDelay = 0;
    }

    if (msg.dst == 'background') {
        var func = messageHandlers[msg.type];
        if (func) {
            func(msg);
        } else {
            console.log("[SGActions/background] Unknown message type:", msg);
        }

    } else if (msg.dst == 'native') {
        try {
            nativePort.postMessage(msg)
        } catch (e) {

            // This is a bit of an awkward situation, because they have
            // already sent us a message (potentially a dispatch), and we
            // were unable to send it. We could try to connect and try again,
            // or bounce it back to them.
            console.log("[SGActions] Native errored:", e);
            broadcast({
                src: 'background',
                dst: 'page',
                type: 'disconnect',
                error: e.toString()
            })

        }

    } else if (msg.dst.tab_id) {

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
        console.log("[SGActions] background cannot route:", msg);

    }

}


var messageHandlers = {};

messageHandlers.hello = function(msg) {
    routeMessage({
        src: 'background',
        dst: msg.src,
        type: 'elloh',
    });
};

messageHandlers.elloh = function(msg) {
    // Forward the reconnection "hello" response to all open pages so they
    // know the connection is back up.
    if (msg.src == 'native') {
        msg.src = 'background';
        msg.dst = 'page';
        broadcast(msg);
    }
}



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



// Kick it all off.
connect()

