

var messageHandlers = {};

messageHandlers.hello = function(msg) {
    routeMessage({
        src: 'main',
        dst: msg.src,
        type: 'elloh',
    });
};

messageHandlers.elloh = function(msg) {
    console.log("[SGActions/main] Connected to " + msg.src + ".");
}


var routeMessage = function(msg) {

    if (msg.dst == 'page') {
        window.postMessage({sgactions: msg, from_main: true}, '*');

    } else if (msg.dst == 'background' || msg.dst == 'native') {
        getPort().postMessage(msg);

    } else if (msg.dst == 'main') {
        var func = messageHandlers[msg.type];
        if (func) {
            func(msg);
        } else {
            console.log("[SGActions/main] Unknown message type:", msg);
        }

    } else {
        console.log("[SGActions/main] Cannot route message:", msg);

    }
}

var onDisconnect = function() {
    console.log("[SGActions/main] Background disconnected.")
    port = null
    // Let the page know.
    routeMessage({
        src: 'main',
        dst: 'page',
        type: 'disconnect'
    })
}

var _port = null;
var getPort = function() {
    
    if (_port != null) {
        return _port;
    }

    console.log('[SGActions/main] Connecting to background.')
    _port = chrome.runtime.connect();
    _port.onMessage.addListener(routeMessage);
    _port.onDisconnect.addListener(onDisconnect);
    _port.postMessage({
        dst: 'background',
        src: 'main',
        type: 'hello',
    })

    return _port;

}





window.addEventListener("message", function(e) {
    if (e.source != window) return; // Must be from this page.
    if (!e.data.sgactions) return; // Must be sgactions.
    if (e.data.from_main) return; // Must not be from us.
    routeMessage(e.data.sgactions);
})


function getPageURL(url) {
    return chrome.extension.getURL('page/' + url)
}

function injectCSS(url) {
    var link = document.createElement("link");
    link.setAttribute("rel", "stylesheet");
    link.setAttribute("type", "text/css");
    link.setAttribute("href", url);
    document.head.appendChild(link);
}

function injectJS(url) {
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.src = url
    document.head.appendChild(script);
}


injectCSS(getPageURL("css/icons/silk.css"));
// injectCSS(getPageURL("css/icons/fatcow.css"));
injectCSS(getPageURL("css/sgactions.css"));
// injectCSS('https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css');

injectJS(getPageURL("ui.js"));
injectJS(getPageURL("core.js")); // Depends on UI.
injectJS(getPageURL("menu.js")); // Depends on UI.



// Go!
getPort();

