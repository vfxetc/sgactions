// We need to get around Chrome's sandbox and run out script in the actual
// window. This does that, but still results in a warning being issued that the
// script is being transfered with the MIME type text/plain. I don't think
// there is anything we can do about it.

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
inject_css(chrome.extension.getURL("rich_shotgun_actions.css"));
inject_js(chrome.extension.getURL("rich_shotgun_actions.js"));
