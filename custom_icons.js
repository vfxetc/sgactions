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
                    
                    var m;
                    
                    // Look for an icon name.
                    m = /^\s*\[([\w-]+)\]\s*(.+)$/.exec(this.items[i].html || '');
                    if (m) {
                        this.items[i].icon_name = 'silk-icon silk-icon-' + m[1];
                        this.items[i].html = m[2];
                    } else {
                        this.items[i].icon_name = 'silk-icon silk-icon-brick';
                    }
                    
                    // Look for a heading.
                    m = /^([^:]+):\s*(.+)$/.exec(this.items[i].html || '');
                    if (m) {
                        if (last_heading != m[1]) {
                            this.items[i].heading = m[1];
                        }
                        this.items[i].html = m[2];
                        last_heading = m[1];
                    } else {
                        if (last_heading) {
                            this.items[i].line = true;
                        }
                        last_heading = null;
                    }
                    
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