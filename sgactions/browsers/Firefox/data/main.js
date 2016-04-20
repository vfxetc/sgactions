
console.error('SGActions contentScript.js')

for (var i = 0; i < self.options.styles.length; i++) {
    var link = document.createElement("link");
    link.setAttribute("rel", "stylesheet");
    link.setAttribute("type", "text/css");
    link.setAttribute("href", self.options.styles[i]);
    document.head.appendChild(link);
}
for (var i = 0; i < self.options.scripts.length; i++) {
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.src = self.options.scripts[i]
    document.head.appendChild(script);
}
