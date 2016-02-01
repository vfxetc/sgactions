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
        },

        showAlert: function(msg) {
            
            SGActions.preemptScheduledMessages()
            SGActions.hideProgress()

            try {
                var dialog = new SG.AlertDialog({
                    title: msg.title || 'SGActions',
                    body: (msg.message || 'Alert!').replace(/\n/g, '<br>'),
                    action: {extra_cls: 'blue_button'},
                    width: '800px',
                }, {})
                dialog.present();            
            } catch (e) {
                if (msg.message) {
                    alert(msg.message)
                }
                console.log('[SGActions]', e, 'during alert', msg);
                console.traceback();
            }
        },

        showMessage: function(msg) {

            if (msg.message) {
                msg.html = msg.message;
                msg.message = undefined;
            }

            if (msg.details) {
                msg.title = msg.html
                msg.html += ' <a href="javascript:SGActions.showMessageDetails()">Details</a>'
            }

            // Defaults.
            if (msg.close_x === undefined) {
                msg.close_x = true;
            }
            if (msg.type) {
                msg.message_type = 'sgactions_' + msg.type
            }
            if (!msg.message_type) {
                msg.message_type = 'sgactions_generic'
            }

            SG.Message.show(msg);

        },

        showMessageDetails: function() {
            
            var msg = SG.Message.last_config
            if (!msg.details) {
                return
            }

            SGActions.showAlert({
                title: msg.title,
                message: msg.details
            });

        },

        // Defer showing a message for a brief period, only showing it if
        // no other messages were shown.
        scheduleMessage: function(msg, timeout) {

            var counter = ++SGActions._scheduleCounter

            // We are assuming that we can mutate the last_config without
            // Shotgun noticing and/or caring.
            if (!SG.Message.last_config) {
                SG.Message.last_config = {}
            }
            SG.Message.last_config._scheduleCounter = counter

            setTimeout(function() {
                if (SG.Message.last_config._scheduleCounter == counter) {
                    SGActions.showMessage(msg)
                }
            }, timeout || 1000)

        },
        _scheduleCounter: 0,

        preemptScheduledMessages: function() {
            if (!SG.Message.last_config) {
                SG.Message.last_config = {}
            }
            SG.Message.last_config._scheduleCounter = undefined;
        },

        // Hide any messages, optionally of the given type.
        hideMessage: function(type) {
            // Need to look for SG.Message since the "hello" may arrive
            // before Shotgun is done loading.
            if (SG.Message && (!type || type == SG.Message.message_type)) {
                SG.Message.hide()
            }
        },

        hideProgress: function() {
            SGActions.hideMessage('sgactions_progress')
        },

        showConfirm: function(msg, callback, scope) {
            var dialog = new SG.ConfirmDialog({
                title: msg.title || "SGActions",
                body: msg.body || msg.message // Perhaps too forgiving.
            }, scope || this);
            dialog.go().then(function() {
                SGActions._confirmResponse(callback, dialog, true)
            }, function() {
                SGActions._confirmResponse(callback, dialog, false)
            })
            return dialog;
        },

        _confirmResponse: function(callback, dialog, value) {
            var data = {}
            // var inputs = dialog.body_dom.getElementsByTagName('input')
            callback(value, {})
        },

        _selectRowTemplate: new Ext.Template(
            '<div class="sgactions-select-row">',
                '<input type="radio" id="sgactions-select-input-{name}" name="sgactions-select" value="{name}" {checked}/>',
                '<label for="sgactions-select-input-{name}">{label}</label>',
            '</div>'
        ),

        showSelect: function(msg, callback, scope) {

            var body = msg.prologue ? '<div class="sgactions-select-prologue">' + msg.prologue + '</div>' : '';
            var hasDefault = false;
            for (var i = 0; i < msg.options.length; i++) {
                var option = msg.options[i];
                option['checked'] = option['checked'] ? 'checked' : '';
                hasDefault = hasDefault || option['checked'];
                body += SGActions._selectRowTemplate.apply(option);
            }
            body += msg.epilogue ? '<div class="sgactions-select-epilogue">' + msg.epilogue + '</div>' : '';

            var dialog = new SG.ConfirmDialog({
                title: msg.title || 'SGActions Selector',
                body: body,
                ok_action: {extra_cls: 'blue_button'},
            }, scope || this);
            dialog.go().then(function() {
                SGActions._selectResponse(callback, dialog, true)
            }, function() {
                SGActions._selectResponse(callback, dialog, false)
            })

            if (!hasDefault) {
                var okButton = dialog.container.dom.getElementsByTagName('button')[1];
                okButton.disabled = true;
                var onInput = function() {
                    okButton.disabled = false;
                }
                var inputs = dialog.body_dom.getElementsByTagName('input');
                for (var i = 0; i < inputs.length; i++) {
                    inputs[i].addEventListener('change', onInput, false);
                }
            }

            return dialog
        },

        _selectResponse: function(callback, dialog, value) {
            if (!value) {
                callback(null)
            } else {
                var inputs = dialog.body_dom.getElementsByTagName('input');
                for (var i = 0; i < inputs.length; i++) {
                    var input = inputs[i];
                    if (input.checked) {
                        callback(input.value)
                        return
                    }
                }
            }
        }

    }


    window.addEventListener("message", function(e) {

        if (e.source != window) return; // Must be from this window (i.e. main or page).
        if (!e.data.sgactions) return; // Must be sgactions.
        if (e.data.sgactions.dst != 'page') return; // Must be sent to us.

        var msg = e.data.sgactions;

        switch(msg.type) {

            case 'elloh': // Reply to our hello.
                console.log('[SGActions] native connect with capabilities:', msg.capabilities);
                SGActions.nativeCapabilities = msg.capabilities;

                // Notify them if this is a reconnect.
                if (SGActions._didDisconnect) {
                    SGActions.showMessage({
                        html: 'Western Post plugin reconnected.',
                        type: 'connected',
                    })
                    // Hide it in 2s.
                    setTimeout(function() {
                        SGActions.hideMessage('sgactions_connected')
                    }, 2000)
                }

                break;

            case 'error':
                console.log('[SGActions] native error:', msg['error']);
                break;

            case 'disconnect':

                console.log('[SGActions]', msg.src, 'disconnected');

                // Forget that we can do anything until told otherwise.
                SGActions.nativeCapabilities = {};
                SGActions._didDisconnect = true;
                if (msg.src == 'main') {
                    SGActions.showMessage({
                        html: 'Western Post plugin crashed; please refresh Shotgun.',
                        type: 'crashed',
                        close_x: false
                    })
                } else {
                    SGActions.showMessage({
                        html: 'Western Post plugin disconnected; reconnecting...',
                        type: 'disconnect',
                        close_x: false
                    })
                }

                break;

            case 'result':
                // We don't do anything with these except hide the "running" notifications.
                console.log('[SGActions] dispatch returned')
                SGActions.hideMessage('sgactions_dispatch')
                break

            case 'notify':
            case 'progress':
                SGActions.showMessage(msg)
                break

            case 'alert':
                SGActions.showAlert(msg)
                break;

            case 'confirm':
                SGActions.showConfirm(msg, function(value) {
                    SGActions.postNative({
                        type: 'user_response',
                        value: value,
                        session: msg.session // So it knows what message it was for.
                    })
                })
                break;

            case 'select':
                SGActions.showSelect(msg, function(value) {
                    SGActions.postNative({
                        type: 'user_response',
                        value: value,
                        session: msg.session // So it knows what message it was for.
                    })
                })
                break;

            default:
                console.log('[SGActions] unknown message:', msg);
        }
    })

    // Say hello to the native messenger; it will tell is what it's capabilities are.
    SGActions.postNative({
        type: 'hello',
        capabilities: {
            notify : SG.Message !== undefined ? 1 : 0,
            alert  : SG.AlertDialog           ? 1 : 0,
            confirm: SG.ConfirmDialog         ? 1 : 0,
            select : SG.ConfirmDialog         ? 1 : 0    
        }
    })



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

        // SG.StreamDetailHeader is for just a single entity.
        if (entity_page.entity) {
            var entity = entity_page.entity;
            var record = entity_page.entity_data[entity.type][entity.id].record;
            var data = clone(record.row.data);
            data.type = entity.type;
            create_self_links(data);
            console.log(data);
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
            create_self_links(entities[i]);
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


    // monkey-patch base action handler (for page-level actions, etc.)
    var original_action = window.SG.Widget.Base.prototype.on_custom_external_action;
    window.Ext.override(window.SG.Widget.Base, {
        on_custom_external_action: function(selected_entity, action_url, action_poll_for_data_updates) {

            // Don't do anything if it isn't one of ours.
            if (!SGActions.nativeCapabilities.dispatch || action_url.indexOf("sgaction:") != 0) {
                return original_action.apply(this, arguments);
            }

            try {

                // Lifted from Shotgun's source.
                var req = {
                    user_id: SG.globals.current_user.id,
                    user_login: SG.globals.current_user.login,
                    session_uuid: SG.globals.session_uuid,
                    entity_type: selected_entity.type,
                    selected_ids: selected_entity.id,
                    ids: selected_entity.id,
                    server_hostname: SG.globals.hostname,
                    title: SG.schema.entity_types[selected_entity.type].display_name + ' ' + selected_entity.id
                };
                var project = this.single_project_from_context();
                if (project) {
                    req.project_name = project.name;
                    req.project_id = project.id;
                    req.title = req.project_name + ' - ' + req.title;
                }
                
                // SGActions!
                var url = action_url + "?" + Ext.urlEncode(req);
                SGActions.postNative({
                    type: 'dispatch',
                    url: url
                })

                // Lifted from Shotgun's source.
                if (action_poll_for_data_updates) {
                    SG.Repo.request_news()
                }

                SGActions.scheduleMessage({
                    html: 'Running ' + action_url.substr(9),
                    close_x: true,
                    type: 'dispatch'
                })

            } catch (e) {
                console.log('[SGActions] error in on_custom_external_action:', err);
                return original_action.apply(this, arguments);
            }

        }
    })

    // monkey-patch context menu launcher
    var original_launch = window.SG.Widget.EntityQuery.EntityQueryPage.prototype.custom_external_action_launch;
    window.Ext.override(window.SG.Widget.EntityQuery.EntityQueryPage, {
        custom_external_action_launch: function() {

            try {

                var base_url = this.custom_external_action.base_url;
                var poll_for_data_updates = this.custom_external_action.poll_for_data_updates;

                // Don't do anything if it isn't one of ours.
                if (!SGActions.nativeCapabilities.dispatch || base_url.indexOf("sgaction:") != 0) {
                    return original_launch.apply(this, arguments);
                }

                // Lifted from Shotgun's source.
                var url = base_url + "?" + Ext.urlEncode(this.custom_external_action);

                // SGActions!
                console.log('[SGActions] native dispatch:', base_url);
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

                SGActions.scheduleMessage({
                    html: 'Running ' + base_url.substr(9),
                    close_x: true,
                    type: 'dispatch'
                })

            } catch(err) {

                console.log('[SGActions] error in custom_external_action_launch:', err);

                // Restore state, and fall back onto the original.
                if (base_url != undefined) {
                    this.custom_external_action.base_url = base_url;
                }
                if (poll_for_data_updates != undefined) {
                    this.custom_external_action.poll_for_data_updates = poll_for_data_updates;
                }
                return original_launch.apply(this, arguments);

            }


        }
    })

} // load check

