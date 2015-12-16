

var port;

var routeMessage = function(msg) {
    if (msg.dst == 'page') {
        window.postMessage({sgactions: msg}, '*');
    } else {
        console.log('[SGActions] main cannot route message:', msg);
    }
}

var onDisconnect = function(event) {
    console.log('[SGActions] background disconnected')
    port = null
    routeMessage({
        src: 'main',
        dst: 'page',
        type: 'disconnect'
    })
}

var connect = function() {
    console.log('[SGActions] connecting to background')
    port = chrome.runtime.connect();
    port.onMessage.addListener(routeMessage);
    port.onDisconnect.addListener(onDisconnect);
}
connect();

window.addEventListener("message", function(e) {
    
    if (e.source != window) return; // Must be from this page.
    if (!e.data.sgactions) return;  // Must be sgactions.

    var msg = e.data.sgactions;

    // Redirect messages to the background to it.
    if (msg.dst == 'background' || msg.dst == 'native') {
        port.postMessage(msg);
    }

})


function inject_node(node) {
    (document.head || document.body || document.documentElement).appendChild(node);
}

function inject_css(url) {
    var link = document.createElement("link");
    link.setAttribute("rel", "stylesheet");
    link.setAttribute("type", "text/css");
    link.setAttribute("href", url);
    inject_node(link);
}

function inject_js(url) {
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.src = url
    inject_node(script);
}

inject_css(chrome.extension.getURL("silk/silk-icons.css"));
inject_css(chrome.extension.getURL("page.css"));
inject_js(chrome.extension.getURL("page.js"));

