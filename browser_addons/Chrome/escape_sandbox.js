// We need to get around Chrome's sandbox and run out script in the actual
// window. This does that, but still results in a warning being issued that the
// script is being transfered with the MIME type text/plain. I don't think
// there is anything we can do about it.

function inject_script(url) {
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.src = url;
    (document.head || document.body || document.documentElement).appendChild(script);
}

inject_script(chrome.extension.getURL("rich_shotgun_actions.js"));
