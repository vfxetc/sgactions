if (window.SGActions != undefined) {
    console.log('SGActions already loaded; are there more than one?')

} else if (window.SG == undefined) {
    console.log('SGActions loaded before Shotgun; this is OK on the login page.');

} else {

    console.log('[SGActions] loaded')

    SGActions = {
        nativeCapabilities: {},
        postNative: function(msg) {
            msg.src = 'page';
            msg.dst = 'native';
            window.postMessage({sgactions: msg}, '*')
        }
    }

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
            case 'error':
                console.log('[SGActions] native error:', msg['error']);
                console.log('[SGActions] forgetting native connection');
                SGActions.nativeCapabilities = {};
                break;
            case 'disconnect':
                console.log('[SGActions] native disconnected');
                SGActions.nativeCapabilities = {};
                break;
            default:
                console.log('[SGActions] unknown message:', msg);
        }
    })

    // Say hello to the native messenger; it will tell is what it's capabilities are.
    SGActions.postNative({type: 'hello'})



    var create_self_links = function(entity, _seen) {
        
        // Recursion guard (for extra safety).
        _seen = _seen || {}
        _seen[entity.type] = _seen[entity.type] || {}
        if (_seen[entity.type][entity.id]) {
            return;
        }
        _seen[entity.type][entity.id] = true;

        entity[entity.type] = entity
        for (var key in entity) {
            if (entity.hasOwnProperty(key) && entity[key] && entity[key].type && entity[key].id) {
                create_self_links(entity[key], _seen)
            }
        }

    }

    var clone = function(x) {
        return JSON.parse(JSON.stringify(x));
    }

    var get_selected_entities = function(entity_page) {

        var selected_eids = entity_page.selected_entities;
        if (selected_eids.length < 1) {
            return [];
        }

        var content_widget = entity_page.get_content_widget();
        var entity_set = content_widget.get_entity_data_store();
        var entity_type = entity_page.get_content_widget_entity_type();
        var schema_fields = SG.schema.entity_fields[entity_type];
        
        var eid_map = {};
        var entities = [];

        // Copy the basic data for each selected entity.
        for (i = 0; i < selected_eids.length; i++) {
            var eid = selected_eids[i];

            var record = entity_set.id_map[eid];
            var data = clone(record.row.data); // This is fast. Really.

            data.type = entity_type; // Shotgun doesn't store this here.

            eid_map[eid] = data;
            entities.push(data)
        }

        // Extract the data used for grouping (which isn't in the record).
        if (entity_set.grouped) {

            var group_defs = entity_set.grouping;
            var groups = entity_set.groups_with_idx;
            for (i = 0; i < groups.length; i++) {
                var group = groups[i];

                for (j = 0; j < group.ids.length; j++) {
                    var eid = group.ids[j];

                    var entity = eid_map[eid];
                    if (!entity) {
                        // Not selected, so don't care.
                        continue
                    }

                    for (k = 0; k < group_defs.length; k++) {
                        entity[group_defs[k].column] = clone(group.template_values[k])
                    }
                }
            }
        }

        // Provide typed links to self in all entities.
        for (i = 0; i < entities.length; i++) {
            create_self_links(entities[i]);
        }

        return entities;
    }

    var evaluate_filter = function(filter, entity) {

        var attrs = filter[0].split('.')
        var head = entity;
        try {
            for (var i = 0; i < attrs.length; i++) {
                var attr = attrs[i]
                head = head[attr]
            }
        } catch (e) {
            return;
        }

        switch (filter[1]) {
            case 'is':
            case 'eq':
            case '==':
                return head == filter[2];
                break;
            default:
                throw "unknown operator: " + filter[1];
        }

    }

    var evaluate_filter_for_many = function(filter, entities) {
        var totals = {
            pass: 0,
            fail: 0,
            unknown: 0,
            total: 0
        }
        for (var i = 0; i < entities.length; i++) {
            var res = evaluate_filter(filter, entities[i]);
            if (res == undefined) {
                totals.unknown += 1
            } else {
                totals[res ? 'pass' : 'fail'] += 1
            }
            totals.total += 1
        }
        return totals;

    }




    var original_render = window.SG.Menu.prototype.render_menu_items;
    window.Ext.override(window.SG.Menu, {
        render_menu_items: function() {
            
            try {

                var selected = null

                // Parse and set the data.
                for (var i = 0; i < this.items.length; i++) {

                    var item = this.items[i];

                    // The undefined check is our tenuous hold on folders
                    // that are created for ActionMenuItems.
                    if (item.url || (item.order !== undefined && item.disabled === undefined)) {

                        var filter = null;

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

                            filter = rich.f ? JSON.parse(rich.f) : null;
                            
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

                        // Styling for expression.
                        if (filter) {
                            if (selected == null) {
                                selected = get_selected_entities(this.parent)
                            }
                            var totals = evaluate_filter_for_many(filter, selected);
                            if (totals.pass && totals.fail) {
                                item.html = item.html + '<span class="sgactions-filter-count"> (' + totals.pass + ' of ' + totals.total + ')</span>'
                                item.item_class = 'sgactions-filter-passfail'
                            } else if (totals.fail) {
                                item.disabled = true;
                            }
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
                console.log('[SGActions] error in render_menu_items:', err);
                console.log(err.stack);
            }
            
            // this.items.push({html: "Submenu test", submenu:{items:[{html: 'Child'}]}});
            
            return original_render.apply(this, arguments);
        }
    });


    var original_launch = window.SG.Widget.EntityQuery.EntityQueryPage.prototype.custom_external_action_launch;
    window.Ext.override(window.SG.Widget.EntityQuery.EntityQueryPage, {
        custom_external_action_launch: function() {

            var base_url, poll_for_data_updates;

            try {

                base_url = this.custom_external_action.base_url;
                poll_for_data_updates = this.custom_external_action.poll_for_data_updates;

                if (SGActions.nativeCapabilities.dispatch && base_url.indexOf("sgaction:") === 0) {

                    console.log('[SGActions] native dispatch:', base_url);

                    // Lifted from Shotgun's source.
                    var url = base_url + "?" + Ext.urlEncode(this.custom_external_action);

                    SGActions.postNative({
                        type: 'dispatch',
                        url: url
                    })

                    // Lifted from Shotgun's source.
                    delete this.custom_external_action.base_url;
                    delete this.custom_external_action.poll_for_data_updates;
                    var content_widget = this.get_content_widget();
                    content_widget.hide_loading_overlay();
                    if (poll_for_data_updates) {
                        SG.Repo.request_news()
                    }
                    return

                }

            } catch(err) {
                console.log('[SGActions] error in custom_external_action_launch:', err);
                if (base_url != undefined) {
                    this.custom_external_action.base_url = base_url;
                }
                if (poll_for_data_updates != undefined) {
                    this.custom_external_action.poll_for_data_updates = poll_for_data_updates;
                }
            }

            return original_launch.apply(this, arguments);

        }
    })

} // load check

