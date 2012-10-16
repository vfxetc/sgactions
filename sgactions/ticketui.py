from __future__ import absolute_import

import traceback
import time
import sys
import subprocess
import platform
import tempfile

from PyQt4 import QtCore, QtGui
Qt = QtCore.Qt

import shotgun_api3_registry

from . import tickets


class Dialog(QtGui.QDialog):
    
    def __init__(self, exceptions=None):
        super(Dialog, self).__init__()
        self._exception_list = list(exceptions or [])
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle('Open A Ticket')
        self.setMinimumSize(400, 300)
        self.setLayout(QtGui.QFormLayout())
        
        self._exception = QtGui.QComboBox()
        self._exception.addItem('None')
        for exc_type, exc_value, exc_traceback in self._exception_list:
            self._exception.addItem('%s: %s [%s]' % (exc_type.__name__, exc_value,
                tickets.exception_hash(exc_type, exc_value, exc_traceback),
            ))
        self._exception.setCurrentIndex(self._exception.count() - 1)
        self.layout().addRow("Exception", self._exception)
        
        self._ticket = QtGui.QComboBox()
        self._ticket.addItem("New")
        self.layout().addRow("Ticket", self._ticket)
        
        self._title = QtGui.QLineEdit('Title')
        self.layout().addRow("Title", self._title)
        
        self._description = QtGui.QTextEdit('Description')
        self._description.focusInEvent = lambda *args: self._description.selectAll()
        self.layout().addRow("Description", self._description)
        
        self._screenshot_path = None
        self._screenshot = QtGui.QLabel()
        self._screenshot.setFixedSize(100, 100)
        self._screenshot.setFrameShadow(QtGui.QFrame.Sunken)
        self._screenshot.setFrameShape(QtGui.QFrame.Panel)
        self._screenshot.mouseReleaseEvent = self._on_screenshot
        self.layout().addRow("Screenshot", self._screenshot)
        
        buttons = QtGui.QHBoxLayout()
        self.layout().addRow("", buttons)
        
        # button = QtGui.QPushButton('Add Screenshot')
        # buttons.addWidget(button)
        
        buttons.addStretch()
        
        button = QtGui.QPushButton('Submit')
        button.clicked.connect(self._on_submit)
        buttons.addWidget(button)
        
        self._title.selectAll()
    
    def _on_screenshot(self, *args):
        self.hide()
        path = tempfile.NamedTemporaryFile(suffix=".png", prefix="tanktmp", delete=False).name
        if platform.system() == "Darwin":
            # use built-in screenshot command on the mac
            proc = subprocess.Popen(['screencapture', '-mis', path])
        else:
            proc = subprocess.Popen(['import', path])
        proc.wait()
        self.show()
        
        self._screenshot_path = path
        pixmap = QtGui.QPixmap(path).scaledToHeight(100, Qt.SmoothTransformation)
        self._screenshot.setPixmap(pixmap)
        self._screenshot.setFixedSize(pixmap.size())
            
    def _on_submit(self, *args):
        exc_uuid, ticket_id, reply_id = tickets.create_ticket(
            title=str(self._title.text()),
            description=str(self._description.toPlainText()),
            attachments=[self._screenshot_path],
        )
        self.close()
        QtGui.QMessageBox.information(None,
            'Ticket Created',
            'Ticket #%d has been created on Shotgun' % ticket_id,
        )


__also_reload__ = [
    'sgactions.tickets',
]

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
        