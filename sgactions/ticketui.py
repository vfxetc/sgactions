from __future__ import absolute_import

import traceback
import time
import sys
import subprocess
import platform
import tempfile
import os

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
        self._exception.addItem('None', None)
        for exc_type, exc_value, exc_traceback in self._exception_list:
            self._exception.addItem(
                '%s: %s [%s]' % (exc_type.__name__, exc_value, tickets.exception_uuid(exc_type, exc_value, exc_traceback)),
                (exc_type, exc_value, exc_traceback),
            )
        self._exception.setCurrentIndex(self._exception.count() - 1)
        self._exception.currentIndexChanged.connect(self._on_exception)
        self.layout().addRow("Exception", self._exception)
        
        # self._ticket = QtGui.QComboBox()
        # self._ticket.addItem("New")
        # self.layout().addRow("Ticket", self._ticket)
        
        self._title_label = QtGui.QLabel("Title")
        self._title = QtGui.QLineEdit('Bug Report')
        self.layout().addRow(self._title_label, self._title)
        
        self._description = QtGui.QTextEdit('Please describe the problem, and any steps to reproduce it and/or fix it.')
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
        
        self._description.selectAll()
        self._on_exception(self._exception.currentIndex())
    
    def _on_exception(self, exc_index):
        exc_info = self._exception.itemData(exc_index).toPyObject()
        self._title_label.setVisible(not exc_info)
        self._title.setVisible(not exc_info)
    
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
    
    def description(self):
        return str(self._description.toPlainText())
    
    def _get_reply_data(self):
        return [
            ('User Comment', str(self._description.toPlainText())),
            ('OS Environment', dict(os.environ)),
        ]
    
    def _on_submit(self, *args):
        
        exc_index = self._exception.currentIndex()
        exc_info = self._exception.itemData(exc_index).toPyObject()
        if exc_info:
            title = None
        else:
            exc_info = exc_info or (None, None, None)
            title = str(self._title.text())
        ticket_id = tickets.get_ticket_for_exception(*exc_info, title=title)
        reply_id = tickets.reply_to_ticket(ticket_id, self._get_reply_data(), user_id=tickets.guess_user_id())
        if self._screenshot_path:
            tickets.attach_to_ticket(ticket_id, self._screenshot_path)
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
        