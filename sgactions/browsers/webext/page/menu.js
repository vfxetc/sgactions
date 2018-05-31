(function() {



var create_deep_links = function(entity, _seen) {
    // Mimicks the appearance of deep-links in the Shotgun API.
    
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
            create_deep_links(entity[key], _seen)
        }
    }

}

var clone = function(x) {
    return JSON.parse(JSON.stringify(x));
}

var get_selected_entities = function(entity_page) {

    // SG.StreamDetailHeader is for just a single entity.
    if (entity_page.entity) {
        var entity = entity_page.entity;
        var record = entity_page.entity_data[entity.type][entity.id].record;
        var data = clone(record.row.data);
        data.type = entity.type;
        create_deep_links(data);
        return [data];
    }

    // SG.Widget.EntityQuery.EntityQueryPage is the main grid layout.
    var selected_eids = entity_page.selected_entities;
    if (!selected_eids || selected_eids.length < 1) {
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
        create_deep_links(entities[i]);
    }

    return entities;
}

var evaluate_filter = function(filter, entity) {

    // recurse for more complicated filters
    if (typeof filter[0] != "string") {
        for (var i = 0; i < filter.length; i++) {
            if (!evaluate_filter(filter[i], entity)) {
                return false;
            }
        }
        return true;
    }
    
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

        case 'is': // in Shotgun
        case 'eq':
        case '==':
            return head == filter[2];

        case 'is_not': // in Shotgun
        case 'not_eq':
        case '!=':
            return head != filter[2];

        case 'starts_with': // in Shotgun
            return filter[2].indexOf(head) == 0;

        case 'contains': // in Shotgun
        case 'in':
            return filter[2].indexOf(head) != -1;

        case 'not_contains': // in Shotgun
        case 'not_in':
            return filter[2].indexOf(head) == -1;

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

        var res;
        try {
            res = evaluate_filter(filter, entities[i]);
        } catch (e) {
            console.log('error during evaluate_filter', filter, entities[i], e);
            res = undefined;
        }

        if (res == undefined) {
            totals.unknown += 1
        } else {
            totals[res ? 'pass' : 'fail'] += 1
        }
        totals.total += 1
    }
    return totals;

}

var expand_icon_name = function(icon) {
    
    // Silk looks like:
    //   silk-icon silk-icon-NAME
    // FontAwesome looks like:
    //   fa fa-NAME

    m = /^(fa|silk|fatcow)(?:-icon)?-([\w-]+)$/.exec(icon)
    if (m) {
        return m[1] + ' ' + m[1] + '-' + m[2];
        if (m[1] == 'silk') {
            return 'silk silk-' + m[2]
        } else {
            return m[1] + ' ' + icon
        }
    }

    // Assume silk for simple ones.
    if (/^[\w-]+$/.test(icon)) {
        return 'silk silk-' + icon
    }
    return icon

}


// monkey-patch icons
// For some reason doing it with Ext.override isn't playing nicely.
var original_entity_icon_name = window.SG.schema.entity_icon_name;
var iconLogged = {};
window.SG.schema.entity_icon_name = function(name) {
    // console.log('icon for', name)

    try {
        var icon = localStorage['sga_icon_' + name]
        if (icon) {
            icon = expand_icon_name(icon);
            if (!iconLogged[name]) {
                console.log('[SGActions] replacing', name, 'icon with:', icon)
                iconLogged[name] = true
            }
            return icon;
        }
    } catch (e) {
        console.log('[SGActions] error in entity_icon_name:', e);
    }

    // return 'silk-icon silk-icon-bell'
    return original_entity_icon_name.call(this, name)
}


// monkey-patch menu render (for icons, filtering, etc.)
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

                    // Method 1 of encoding rich data; the second path segment of the URL:
                    // e.g.: `sgactions:xxx/h=Heading&t=Title&i=icon&f={json-of-filter}`
                    // This is not prefered since there are URL-length limitations when
                    // using the fallback dispatch methods, also because it cannot affect
                    // folders.
                    if (/^sgaction/.test(item.url || '')) {

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
                        item.icon_name = expand_icon_name(rich.i || 'brick')
                        item.heading = rich.h;

                        filter = rich.f ? JSON.parse(rich.f) : null;
            
                    }

                    // Method 2: Rich data in the title itself, e.g.:
                    // "Heading / Title"
                    var m = /^\s*(.+?)\s+\/\s+(.+?)\s*$/.exec(item.html || '');
                    if (m) {
                        item.heading = m[1];
                        item.html = m[2];
                    }

                    // Icon in square-brackets at end: "Title [icon]"
                    m = /^(.+?)\s*\[(.+?)\]$/.exec(item.html || '');
                    if (m) {
                        item.html = m[1]
                        item.icon_name = expand_icon_name(m[2])
                    }

                    // Evalute the filters, and disable/style the results.
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

            // Collapse identical headings, and parse icons.
            var current_heading = null;
            for (var i = 0; i < this.items.length; i++) {

                if (this.items[i].heading != current_heading) {

                    // Create all-new heading objects because they have
                    // icons as of (approx.) Shotgun 7.
                    if (this.items[i].heading) {

                        var item = {
                            heading: this.items[i].heading
                        }

                        // Icon in square-brackets at end: "Title [icon]"
                        m = /^(.+?)\s*\[(.+?)\]$/.exec(item.heading || '');
                        if (m) {
                            item.heading = m[1];
                            item.icon_name = 'silk-icon silk-icon-' + m[2];
                        }

                        this.items.splice(i, 0, item);
                        i++; // skip it during iteration

                    } else {

                        // Add a line to seperate from the header.
                        this.items.splice(i, 0, {line: true});
                        i++;

                    }

                    current_heading = this.items[i].heading;

                }

                // Remove the heading from the items themselves.
                this.items[i].heading = null;
                
            }

            // Remove double lines before headline changes.
            // An item with a "heading" implies a line, but there
            // is an item `{line: true}` before our ActionMenuItems.
            for (var i = 1; i < this.items.length; i++) {
                if ((this.items[i].line || this.items[i].heading) && this.items[i-1].line && !this.items[i-1].html) {
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


// monkey-patch base action handler (for page-level actions, etc.)
var original_action = window.SG.Widget.Base.prototype.custom_external_action_launcher;
window.Ext.override(window.SG.Widget.Base, {
    custom_external_action_launcher: function(req, ami) {

        // console.log('HERE', req, ami)
        
        try {
            // Strip off the scheme, and any legacy rich data.
            var m = /^sgactions?:([^\/]+)(\/|$)/.exec(ami.url)
            if (m && SGActions.nativeCapabilities.dispatch) {

                var entrypoint = m[1]
                
                SGActions.postNative({
                    type: 'dispatch',
                    entrypoint: m[1],
                    kwargs: req,
                })

                SGActionsUI.scheduleMessage({
                    html: 'Running ' + entrypoint,
                    close_x: true,
                    type: 'dispatch'
                })

                return
            }

        } catch (e) {
            console.log('[SGActions] error in custom_external_action_launcher:', e)
        }

        return original_action.apply(this, arguments)

    }
})




})(); // Closure
