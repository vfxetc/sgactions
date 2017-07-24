(function() {

if (window.SGActions !== undefined) {
    console.log('SGActions already loaded; is there more than one?')
    return
} else if (window.SG === undefined) {
    console.log('SGActions loaded before Shotgun; this is OK on the login page.');
    return
}


console.log('[SGActions] loaded core')


SGActions = {

    nativeCapabilities: {},
    nativeHandlers: {},

    postNative: function(msg) {
        // Assert the envelope.
        msg.src = 'page';
        msg.dst = msg.dst || 'native';
        // Send it to main.js (the content-script).
        window.postMessage({sgactions: msg}, '*')
    },

    _processNativeMessage: function(e) {

        if (e.source != window) return; // Must be from this window (i.e. main.js or page/*.js).
        if (!e.data.sgactions) return; // Must be sgactions.
        if (e.data.sgactions.dst != 'page') return; // Must be addressed to us.

        var msg = e.data.sgactions;
        var func = SGActions.nativeHandlers[msg.type];
        if (func) {
            func(msg)
        } else {
            console.log('[SGActions] unknown native message type', msg.type);
        }
    }

}

window.addEventListener("message", SGActions._processNativeMessage, false);


var hello = function(dst) {
    // Say hello to the native messenger; it will tell is what it's capabilities are.
    SGActions.postNative({
        type: 'hello',
        dst: dst || 'native',
        capabilities: {
            notify : SG.Message !== undefined ? 1 : 0,
            alert  : SG.AlertDialog           ? 1 : 0,
            confirm: SG.ConfirmDialog         ? 1 : 0,
            select : SG.ConfirmDialog         ? 1 : 0
        }
    })
}

// Make the initial connection attempt to the native handler.
hello();


SGActions.nativeHandlers.elloh = function(msg) {

    // This is the reply to our original "hello".

    console.log('[SGActions] native connected with capabilities:', msg.capabilities);
    SGActions.nativeCapabilities = msg.capabilities;

    // Notify them if this is a reconnect.
    if (SGActions._didDisconnect) {
        SGActionsUI.showMessage({
            html: 'SGActions reconnected.',
            type: 'connected',
        })
        // Hide it in 2s.
        setTimeout(function() {
            SGActionsUI.hideMessage('sgactions_connected')
        }, 2000)
    }
}


SGActions.nativeHandlers.error = function(msg) {
    console.log('[SGActions] native error:', msg['error']);
}


SGActions.nativeHandlers.connect = function(msg) {
    // We will only capture this one if we were already open.
    console.log('[SGActions]', msg.src, 'reconnected');
    // Attempt to shake hands with the native handler (again).
    hello();
}

SGActions.nativeHandlers.disconnect = function(msg) {

    console.log('[SGActions]', msg.src, 'disconnected');

    // Forget that we can do anything until told otherwise.
    SGActions.nativeCapabilities = {};
    SGActions._didDisconnect = true;

    if (msg.src == 'main') {
        SGActionsUI.showMessage({
            html: 'SGActions crashed; please refresh Shotgun.',
            type: 'crashed',
            close_x: false
        })
    } else if (msg.src == 'native') {
        SGActionsUI.showMessage({
            html: 'SGActions disconnected; reconnecting...',
            type: 'disconnect',
            close_x: false
        })
    }

}





SGActions.nativeHandlers.result = function() {
    // We don't do anything with these except hide the "running" notifications.
    console.log('[SGActions] dispatch returned')
    SGActionsUI.hideMessage('sgactions_dispatch')
}

SGActions.nativeHandlers.notify =
SGActions.nativeHandlers.progress = function(msg) {
    SGActionsUI.showMessage(msg)

}

SGActions.nativeHandlers.alert = function(msg) {
    SGActionsUI.showAlert(msg)

}

SGActions.nativeHandlers.confirm = function(msg) {
    SGActionsUI.showConfirm(msg, function(ok, form) {
        SGActions.postNative({
            type: 'user_response',
            value: {
                ok: ok,
                form: form || null
            },
            session_token: msg.session_token // So it knows what message it was for.
        })
    })
}

SGActions.nativeHandlers.select = function(msg) {
    SGActionsUI.showSelect(msg, function(value) {
        SGActions.postNative({
            type: 'user_response',
            value: value,
            session_token: msg.session_token // So it knows what message it was for.
        })
    })
}






})() // Definition fence.
