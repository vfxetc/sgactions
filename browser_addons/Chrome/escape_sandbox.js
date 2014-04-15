// We need to get around Chrome's sandbox and run out script in the actual
// window. This does that, but still results in a warning being issued that the
// script is being transfered with the MIME type text/plain. I don't think
// there is anything we can do about it.

function inject_node(node) {
    (document.head || document.body || document.documentElement).appendChild(node);
}

var link = document.createElement("link");
link.setAttribute("rel", "stylesheet");
link.setAttribute("type", "text/css");
link.setAttribute("href", chrome.extension.getURL("silk/silk-icons.css"));
inject_node(link);

var script = document.createElement("script");
script.type = "text/javascript";
script.src = chrome.extension.getURL("rich_shotgun_actions.js");
inject_node(script);
