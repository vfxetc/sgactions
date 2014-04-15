var link = document.createElement("link");
link.setAttribute("rel", "stylesheet");
link.setAttribute("type", "text/css");
link.setAttribute("href", 'https://silk-icons-css.googlecode.com/hg/silk-icons.css');
document.getElementsByTagName('head')[0].appendChild(link);   

console.log('Starting SGActions: rich ActionMenuItems')

var original = window.SG.Menu.prototype.render_menu_items;

window.Ext.override(window.SG.Menu, {
    render_menu_items: function() {
        
        try {
            
            // Parse and set the data.
            for (var i = 0; i < this.items.length; i++) {

                var item = this.items[i];

                // The undefined check is our tenuous hold on folders
                // that are created for ActionMenuItems.
                if (item.url || item.heading === undefined) {
                    
                    // Old method: sgactions have rich data as the last
                    // path segment.
                    if (/^sgaction/.test(item.url || '')) {

                        // Parse the rich data.
                        var rich = {};
                        var m = /^(.+?)\/(.+?)$/.exec(item.url);
                        if (m) {
                            item.url = m[1]
                            var pairs = m[2].split('&');
                            for (var j = 0; j < pairs.length; j++) {
                                var pair = pairs[j].split('=');
                                rich[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1]);
                            }
                        }
                        
                        item.html = rich.t || item.html;
                        item.icon_name = 'silk-icon silk-icon-' + (rich.i || 'brick');
                        item.heading = rich.h;
                        
                    }

                    // New method: Rich data in the title itself, e.g.:
                    // "Heading / Title [icon]"

                    // Heading befor a slash.
                    var m = /^\s*(.+?)\s*\/\s*(.+?)\s*$/.exec(item.html || '');
                    if (m) {
                        item.heading = m[1];
                        item.html = m[2];
                    }

                    // Icon in square-brackets at end.
                    m = /^(.+?)\s*\[(.+?)\]$/.exec(item.html || '');
                    if (m) {
                        item.html = m[1];
                        item.icon_name = 'silk-icon silk-icon-' + m[2];
                    }
                }

            }
            
            // Collapse headings and lines.
            var last_heading = null;
            for (var i = 0; i < this.items.length; i++) {
                
                // Headings.
                if (this.items[i].heading == last_heading) {
                    this.items[i].heading = null
                } else {
                    last_heading = this.items[i].heading;
                }
                
                // Double lines before headline changes.
                if (i && this.items[i].heading && this.items[i-1].line && !this.items[i-1].html) {
                    this.items[i-1].line = false;
                }
            }
            
        
        } catch (err) {
            console.log(err);
        }
        
        // this.items.push({html: "Submenu test", submenu:{items:[{html: 'Child'}]}});
        
        return original.apply(this, arguments);
    }
});


