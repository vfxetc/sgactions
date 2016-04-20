

// The abstract object for connecting to the "background".
var port;
var isChrome = window.chrome != undefined

var routeMessage = function(msg) {
    if (msg.dst == 'page') {
        window.postMessage({sgactions: msg}, '*');
    } else {
        console.log('[SGActions] main cannot route message:', msg);
    }
}

var onDisconnect = function() {
    console.log('[SGActions] background disconnected')
    port = null
    routeMessage({
        src: 'main',
        dst: 'page',
        type: 'disconnect'
    })
}

var connectToBackground = function() {
    console.log('[SGActions] connecting to background')
    if (isChrome) {
        port = chrome.runtime.connect();
        port.onMessage.addListener(routeMessage);
        port.onDisconnect.addListener(onDisconnect);
    } else { // Firefox
        port = self.port;
        port.on('message', routeMessage);
        // There is no disconnect?!
    }
}
connectToBackground();

var sendToBackground = function(msg) {
    if (isChrome) {
        port.postMessage(msg)
    } else {
        port.emit('message', msg)
    }
}

window.addEventListener("message", function(e) {

    // TODO: Figure out why Firefox does not like looking at e.source
    //if (e.source != window) return; // Must be from this page.
    if (!e.data.sgactions) return;  // Must be sgactions.

    var msg = e.data.sgactions;
    // Redirect messages to the background to it.
    if (msg.dst == 'background' || msg.dst == 'native') {
        sendToBackground(msg);
    }

})

function getPageURL(url) {
    if (isChrome) { // Chrome
        return chrome.extension.getURL('page/' + url)
    } else { // Firefox
        return self.options.pageURL + '/' + url
    }
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

injectCSS(getPageURL("css/silk/silk-icons.css"));
injectCSS(getPageURL("css/sgactions.css"));
injectJS(getPageURL("ui.js"));
injectJS(getPageURL("core.js")); // Depends on UI.
injectJS(getPageURL("menu.js")); // Depends on UI.
