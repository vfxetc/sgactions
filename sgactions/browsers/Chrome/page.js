if (window.SGActions != undefined) {
    console.log('SGActions already loaded; are there more than one?')

} else if (window.SG == undefined) {
    console.log('SGActions loaded before Shotgun; this is OK on the login page.');

} else {

    SGActions = {
        nativeCapabilities: []
    }

    console.log('[SGActions] loaded')

    window.addEventListener("message", function(e) {
        if (e.source != window) return; // Must be from this page.
        if (!e.data.sgactions) return; // Must be sgactions.
        if (e.data.sgactions.dst != 'page') return; // Must be sent to us.

        var msg = e.data.sgactions;

        switch(msg.type) {
            case 'hello':
                console.log('[SGActions] native capabilities:', msg.capabilities);
                SGActions.nativeCapabilities = msg.capabilities;
                break;
            default:
                console.log('unknown message:', msg);
        }
    })

    window.postMessage({sgactions: {
        src: 'page',
        dst: 'native',
        type: 'hello'
    }}, '*')



    var original = window.SG.Menu.prototype.render_menu_items;

    window.Ext.override(window.SG.Menu, {
        render_menu_items: function() {
            
            // console.trace();
            console.log(this);

            // this.parent is often EntityQueryPage
            // console.log(this.parent.get_content_widget_entity_type());
            // console.log(this.parent);
            // console.log(this.parent.selected_entities)

            var parent = this.parent;
            var content_widget = parent.get_content_widget();
            var entity_set = content_widget.get_entity_data_store();
            var selected_entities = parent.selected_entities;
            var entity_type = parent.get_content_widget_entity_type();
            var schema_fields = SG.schema.entity_fields[entity_type];

            // console.log(entity_set); // this is "owner"

            for (var i = 0; i < selected_entities.length; i++) {
                rec = entity_set.get_record_by_id(selected_entities[i]);
                // rec.owner.grouping[group_col_i].column describes group names
                // rec.owner.groups_with_idx[group_i].display_values is the display string of the grouped columns
                // rec.owner.groups_with_idx[group_i].template_values is the value of the grouped columns
                // rec.owner.groups_with_idx[group_i].ids is the ids of the entities contained
                console.log(rec);
            }

            this.items.push({
                disabled: false,
                heading: null,
                html: "Testing Injected",
                icon_name: "icon_edit",
                item_selected: { // Callback for when selected.
                    fn: function() {
                        console.log('here, in', this)
                    },
                    scope: this // `this` in the function
                }
            })


            try {
                
                // Parse and set the data.
                for (var i = 0; i < this.items.length; i++) {

                    var item = this.items[i];

                    // The undefined check is our tenuous hold on folders
                    // that are created for ActionMenuItems.
                    if (item.url || (item.order !== undefined && item.disabled === undefined)) {

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
                        var m = /^\s*(.+?)\s+\/\s+(.+?)\s*$/.exec(item.html || '');
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

} // load check

