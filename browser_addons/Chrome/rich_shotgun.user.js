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
        var last_heading = null;
        try {
            for (var i = 0; i < this.items.length; i++) {
                if (this.items[i].url && /^sgaction/.test(this.items[i].url)) {
                    
                    // Parse the rich data.
                    var rich = {};
                    var m = /^(.+?)\/(.+?)$/.exec(this.items[i].url);
                    if (m) {
                        this.items[i].url = m[1]
                        var pairs = m[2].split('&');
                        for (var j = 0; j < pairs.length; j++) {
                            var pair = pairs[j].split('=');
                            rich[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1]);
                        }
                    }
                    
                    // Title.
                    if (rich.t) {
                        this.items[i].html_backup = this.items[i].html;
                        this.items[i].html = rich.t;
                    }
                    
                    // Icon.
                    this.items[i].icon_name = 'silk-icon silk-icon-' + (rich.i || 'brick');
                    
                    // Headings.
                    if (rich.h != last_heading) {
                        this.items[i].heading = rich.h;
                        this.items[i].line = !rich.h;
                    }
                    last_heading = rich.h;
                    
                    console.log('render_menu_items', i, this.items[i]);
                    
                }
            }
        
        } catch (err) {
            console.log(err);
        }
        
        // this.items.push({html: "Submenu test", submenu:{items:[{html: 'Child'}]}});
        
        return original.apply(this, arguments);
    }
});


