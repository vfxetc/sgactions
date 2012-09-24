var link = document.createElement("link");
link.setAttribute("rel", "stylesheet");
link.setAttribute("type", "text/css");
link.setAttribute("href", 'https://silk-icons-css.googlecode.com/hg/silk-icons.css');
document.getElementsByTagName('head')[0].appendChild(link);   


// Define unsafeWindow in browsers where it doesn't exist.
window.unsafeWindow || (
    unsafeWindow = (function() {
        var el = document.createElement('p');
        el.setAttribute('onclick', 'return window;');
        return el.onclick();
    }())
);

console.log('Starting SGActions: rich ActionMenuItems')

var original = unsafeWindow.SG.Menu.prototype.render_menu_items;

unsafeWindow.Ext.override(unsafeWindow.SG.Menu, {
    render_menu_items: function() {
        
        try {
            
            // Parse and set the data.
            for (var i = 0; i < this.items.length; i++) {
                if (this.items[i].url && /^sgaction/.test(this.items[i].url)) {
                    
                    var item = this.items[i];
                    
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


