(function() {

if (window.SGActionsUI !== undefined) {
    console.log('SGActionsUI already loaded; is there more than one?')
    return
} else if (window.SG === undefined) {
    console.log('SGActionsUI loaded before Shotgun; this is OK on the login page.');
    return
}



console.log('[SGActions] loaded UI')


SGActionsUI = {}



var getFormData = function(root) {
    var allData = {}
    var forms = root.getElementsByTagName('form')
    for (var i = 0; i < forms.length; i++) {
        var form = forms[0];
        if (form.name) {
            var data = {};
            allData[form.name] = data;
        } else {
            var data = allData;
        }
        for (var j = 0; j < form.elements.length; j++) {
            var el = form.elements[j];
            data[el.name] = el.value;
        }
    }
    return allData;
}


SGActionsUI.showAlert = function(msg) {
        
    SGActionsUI.preemptScheduledMessages()
    SGActionsUI.hideProgress()

    try {
        var dialog = new SG.AlertDialog({
            title: msg.title || 'SGActions',
            body: (msg.message || 'Alert!').replace(/\n/g, '<br>'),
            action: {extra_cls: 'blue_button'},
            width: '800px',
        }, {})
        dialog.css_class += ' sgactions-dialog sgactions-alert'
        dialog.present();            
    } catch (e) {
        if (msg.message) {
            alert(msg.message)
        }
        console.log('[SGActions]', e, 'during alert', msg);
        console.traceback();
    }
}

SGActionsUI.showMessage = function(msg) {

    if (msg.message) {
        msg.html = msg.message;
        msg.message = undefined;
    }

    if (msg.details) {
        msg.title = msg.html
        msg.html += ' <a href="javascript:SGActionsUI._showMessageDetails()">Details</a>'
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

}

SGActionsUI._showMessageDetails = function() {
    
    var msg = SG.Message.last_config
    if (!msg.details) {
        return
    }

    SGActionsUI.showAlert({
        title: msg.title,
        message: msg.details
    });

}


// Defer showing a message for a brief period, only showing it if
// no other messages were shown.
var scheduleCounter = 0;
SGActionsUI.scheduleMessage = function(msg, timeout) {

    var counter = ++scheduleCounter

    // We are assuming that we can mutate the last_config without
    // Shotgun noticing and/or caring.
    if (!SG.Message.last_config) {
        SG.Message.last_config = {}
    }
    SG.Message.last_config._scheduleCounter = counter

    setTimeout(function() {
        if (SG.Message.last_config._scheduleCounter == counter) {
            SGActionsUI.showMessage(msg)
        }
    }, timeout || 1000)

}

SGActionsUI.preemptScheduledMessages = function() {
    if (!SG.Message.last_config) {
        SG.Message.last_config = {}
    }
    SG.Message.last_config._scheduleCounter = undefined;
}


// Hide any messages, optionally of the given type.
SGActionsUI.hideMessage = function(type) {
    // Need to look for SG.Message since the "hello" may arrive
    // before Shotgun is done loading.
    if (SG.Message && (!type || type == SG.Message.message_type)) {
        SG.Message.hide()
    }
}


SGActionsUI.hideProgress = function() {
    SGActionsUI.hideMessage('sgactions_progress')
}

SGActionsUI.showConfirm = function(msg, callback, scope) {
    var dialog = new SG.ConfirmDialog({
        title: msg.title || "SGActions",
        body: msg.body || msg.message // Perhaps too forgiving.
    }, scope || this);
    dialog.css_class += ' sgactions-dialog sgactions-confirm'
    dialog.go().then(function() {
        var data = getFormData(dialog.body_dom);
        callback(true, data)
    }, function() {
        callback(false)
    })


    return dialog;
}



var selectRowTemplate = new Ext.Template(
    '<div class="sgactions-select-row">',
        '<input type="radio" id="sgactions-select-input-{name}" name="sgactions-select" value="{name}" {checked}/>',
        '<label for="sgactions-select-input-{name}">{label}</label>',
    '</div>'
)

SGActionsUI.showSelect = function(msg, callback, scope) {

    var body = msg.prologue ? '<div class="sgactions-select-prologue">' + msg.prologue + '</div>' : '';
    var hasDefault = false;
    for (var i = 0; i < msg.options.length; i++) {
        var option = msg.options[i];
        option['checked'] = option['checked'] ? 'checked' : '';
        hasDefault = hasDefault || option['checked'];
        body += selectRowTemplate.apply(option);
    }
    body += msg.epilogue ? '<div class="sgactions-select-epilogue">' + msg.epilogue + '</div>' : '';

    var dialog = new SG.ConfirmDialog({
        title: msg.title || 'SGActions Selector',
        body: body,
        ok_action: {extra_cls: 'blue_button'},
    }, scope || this);
    dialog.css_class += ' sgactions-dialog sgactions-select'
    dialog.go().then(function() {
        selectResponse(callback, dialog, true)
    }, function() {
        selectResponse(callback, dialog, false)
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
}

var selectResponse = function(callback, dialog, value) {
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





















})() // Definition fence.