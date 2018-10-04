from __future__ import absolute_import

import contextlib
import os
import subprocess
import sys
import tempfile
import traceback

from uitools.qt import Q

from . import tickets


class Dialog(Q.Widgets.Dialog):
    
    def __new__(cls, *args, **kwargs):
        return super(Dialog, cls).__new__(cls)

    def __init__(self, exceptions=None, allow_no_exception=True):
        super(Dialog, self).__init__()
        
        self._exc_infos = list(exceptions or [])
        self._allow_no_exception = allow_no_exception
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle('Open A Ticket')
        self.setMinimumSize(400, 300)
        self.setLayout(Q.FormLayout())
        
        self._exception = Q.ComboBox()
        
        if self._allow_no_exception:
            self._exception.addItem('None', None)
        
        for exc_type, exc_value, exc_traceback in self._exc_infos:
            uuid = tickets.exception_uuid(exc_type, exc_value, exc_traceback)
            self._exception.addItem('%s: %s [%s]' % (exc_type.__name__, exc_value, uuid))
        self._exception.setCurrentIndex(self._exception.count() - 1)
        self._exception.currentIndexChanged.connect(self._on_exception)
        
        if not self._allow_no_exception and len(self._exc_infos) == 1:
            self.layout().addRow("Exception", Q.Label(self._exception.currentText()))
        else:
            self.layout().addRow("Exception", self._exception)
        
        self._title_label = Q.Label("Title")
        self._title = Q.LineEdit('Bug Report')
        self.layout().addRow(self._title_label, self._title)
        
        self._description = Q.TextEdit('Please describe the problem, and any steps to reproduce it and/or fix it.')
        self._description.focusInEvent = lambda *args: self._description.selectAll()
        self.layout().addRow("Description", self._description)
        
        self._screenshot_path = None
        self._screenshot = Q.Label()
        self._screenshot.setFixedSize(133, 100)
        self._screenshot.setPixmap(Q.Pixmap(os.path.abspath(os.path.join(
            __file__, '..', 'art', 'no_screenshot.png'
        ))).scaledToHeight(100, Q.SmoothTransformation))
        self._screenshot.setFrameShadow(Q.Frame.Sunken)
        self._screenshot.setFrameShape(Q.Frame.Panel)
        self._screenshot.mouseReleaseEvent = self._on_screenshot
        self.layout().addRow("Screenshot", self._screenshot)
        
        buttons = Q.HBoxLayout()
        self.layout().addRow("", buttons)
        
        buttons.addStretch()
        
        button = Q.PushButton('Submit')
        button.clicked.connect(self._on_submit)
        buttons.addWidget(button)
        
        self._description.setFocus()
        self._description.selectAll()
        self._on_exception(self._exception.currentIndex())
    
    def _on_exception(self, exc_index):
        exc_info = self._exc_infos[exc_index]
        self._title_label.setVisible(not exc_info)
        self._title.setVisible(not exc_info)
    
    def _on_screenshot(self, *args):
        self.hide()
        path = tempfile.NamedTemporaryFile(suffix=".png", prefix="tanktmp", delete=False).name
        if sys.platform.startswith('darwin'):
            # use built-in screenshot command on the mac
            proc = subprocess.Popen(['screencapture', '-mis', path])
        else:
            proc = subprocess.Popen(['import', path])
        proc.wait()
        self.show()
        
        self._screenshot_path = path
        pixmap = Q.Pixmap(path).scaledToHeight(100, Q.SmoothTransformation)
        self._screenshot.setPixmap(pixmap)
        self._screenshot.setFixedSize(pixmap.size())
    
    def description(self):
        return str(self._description.toPlainText())
    
    def _get_reply_data(self, exc_info):
        data = [('User Comment', str(self._description.toPlainText()))]
        if exc_info:
            data.append(('Traceback', exc_info))
        data.append(('OS Environment', dict(os.environ)))
        return data
    
    def _on_submit(self, *args):
        exc_index = self._exception.currentIndex()
        exc_info = self._exc_infos[exc_index]
        data = self._get_reply_data(exc_info)
        if exc_info:
            title = None
        else:
            exc_info = exc_info or (None, None, None)
            title = str(self._title.text())
        ticket_id = tickets.get_ticket_for_exception(*exc_info, title=title)
        tickets.reply_to_ticket(ticket_id, data)
        if self._screenshot_path:
            tickets.attach_to_ticket(ticket_id, self._screenshot_path)
        self.close()
        Q.MessageBox.information(None,
            'Ticket Created',
            'Ticket #%d has been created on Shotgun' % ticket_id,
        )


def ticket_current_exception(dialog_class=None):

    msgbox = Q.MessageBox()
    
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    msgbox.setIcon(msgbox.Critical)
    msgbox.setWindowTitle('Python Exception')
    msgbox.setText("Uncaught Python Exception: %s" % exc_type.__name__)
    
    if str(exc_value) == 'super(type, obj): obj must be an instance or subtype of type':
        msgbox.setInformativeText(
            '%s<br/><br/>'
            '<b><i>This appears to be a code reloading issue. '
            'Restarting this program should fix it.</i></b>' % exc_value)
    else:
        msgbox.setInformativeText(str(exc_value))
        msgbox.setDetailedText(traceback.format_exc())
        msgbox.setStyleSheet("* { font-family: monospace; }")

    msgbox.addButton("Submit Ticket", msgbox.AcceptRole)
    
    ignore = msgbox.addButton(msgbox.Ignore)
    msgbox.setDefaultButton(ignore) # <- This does not seem to do much.
    msgbox.setEscapeButton(ignore)
    
    # Returns an int of the button code. Our custom one is 0.
    res = msgbox.exec_()
    if res:
        return False
    
    dialog_class = dialog_class or Dialog
    dialog = dialog_class([(exc_type, exc_value, exc_traceback)], allow_no_exception=False)
    dialog.show()
    
    return True


@contextlib.contextmanager
def ticket_ui_context(reraise=True, pass_through=None, dialog_class=None):
    try:
        yield
    except Exception as e:

        if pass_through and isinstance(e, pass_through):
            raise

        # Dump it out to stdout (or wherever) regardless.
        traceback.print_exc()

        not_ignored = ticket_current_exception(dialog_class=dialog_class)
        if reraise or (reraise is None and not not_ignored):
            raise


def __before_reload__():
    # We have to manually clean this, since we aren't totally sure it will
    # always fall out of scope.
    global dialog
    if dialog:
        dialog.close()
        dialog.destroy()
        dialog = None

dialog = None

def run():
    global dialog
    if dialog:
        dialog.close()
    dialog = Dialog()
    dialog.show()
