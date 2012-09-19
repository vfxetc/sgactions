// ==UserScript==
// @name       SGActions Icons
// @namespace  http://use.i.E.your.homepage/
// @downloadURL http://keyweb/Volumes/VFX/home/mboers/key_tools/sgactions/custom_icons.js
// @version    0.1.1
// @description  Monkey-patch icons onto Shotgun ActionMenuItems
// @match      http*://*.shotgunstudio.com/*
// @copyright  2012+, Western X
// @run-at document-end
// ==/UserScript==

var link = document.createElement("link");
link.setAttribute("rel", "stylesheet");
link.setAttribute("type", "text/css");
link.setAttribute("href", 'https://silk-icons-css.googlecode.com/hg/silk-icons.css');
document.getElementsByTagName('head')[0].appendChild(link);   

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
                    
                    // Title and icon.
                    this.items[i].html = (rich.t || this.items[i].html);
                    this.items[i].icon_name = 'silk-icon silk-icon-' + (rich.i || 'brick');
                    // Headings.
                    if (rich.h != last_heading) {
                        this.items[i].heading = rich.h;
                        this.items[i].line = !rich.h;
                    }
                    last_heading = rich.h;
                    
                }
            }
        
        } catch (err) {
            console.log(err);
        }
        
        // this.items.push({html: "Submenu test", submenu:{items:[{html: 'Child'}]}});
        
        console.log('render_menu_items', this.items);
        return original.apply(this, arguments);
    }
});
